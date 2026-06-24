"""CSMS POC — an OCPP 1.6J central system.

This is the "brain" that a real charger connects to over WebSocket. It handles
the full charging life cycle and stores everything to SQLite (see db.py):

    BootNotification   -> charger announces itself
    Heartbeat          -> keep-alive
    StatusNotification -> available / charging / faulted
    Authorize          -> is this RFID/app token allowed to charge?
    StartTransaction   -> charging began, we hand back a transaction id
    MeterValues        -> live kWh / power readings during the session
    StopTransaction    -> charging ended, we compute kWh for billing

Point a charger's "OCPP server URL" at:  ws://<this-machine-ip>:9000/<charge-point-id>

Run:  python central_system.py
"""
import asyncio
import logging
from datetime import datetime, timezone

import websockets
from ocpp.routing import on
from ocpp.v16 import ChargePoint as BaseChargePoint
from ocpp.v16 import call_result
from ocpp.v16.enums import Action, AuthorizationStatus, RegistrationStatus

import db

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("csms")

LISTEN_HOST = "0.0.0.0"
LISTEN_PORT = 9000
HEARTBEAT_INTERVAL = 30  # seconds we ask the charger to ping us


def now_iso():
    return datetime.now(timezone.utc).isoformat()


# --- A simple allow-list of authorized tokens (RFID / app ids). ---------------
# In production this comes from your users DB. For the POC, accept everything but
# log it, so you can read the real id_tag your card/app sends and whitelist later.
ACCEPT_ALL_TOKENS = True
ALLOWED_TOKENS = {"DEADBEEF", "TEST-TAG-1"}


def is_authorized(id_tag: str) -> bool:
    return ACCEPT_ALL_TOKENS or id_tag in ALLOWED_TOKENS


class ChargePoint(BaseChargePoint):
    @on(Action.boot_notification)
    async def on_boot_notification(self, charge_point_vendor, charge_point_model, **kwargs):
        log.info("[%s] BootNotification vendor=%s model=%s", self.id, charge_point_vendor, charge_point_model)
        db.upsert_charge_point(
            self.id,
            vendor=charge_point_vendor,
            model=charge_point_model,
            serial=kwargs.get("charge_point_serial_number"),
            ts=now_iso(),
            status="Booted",
        )
        return call_result.BootNotification(
            current_time=now_iso(),
            interval=HEARTBEAT_INTERVAL,
            status=RegistrationStatus.accepted,
        )

    @on(Action.heartbeat)
    async def on_heartbeat(self, **kwargs):
        db.upsert_charge_point(self.id, ts=now_iso())
        return call_result.Heartbeat(current_time=now_iso())

    @on(Action.status_notification)
    async def on_status_notification(self, connector_id, error_code, status, **kwargs):
        log.info("[%s] Status connector=%s status=%s error=%s", self.id, connector_id, status, error_code)
        db.upsert_charge_point(self.id, ts=now_iso(), status=status)
        return call_result.StatusNotification()

    @on(Action.authorize)
    async def on_authorize(self, id_tag, **kwargs):
        ok = is_authorized(id_tag)
        log.info("[%s] Authorize id_tag=%s -> %s", self.id, id_tag, "ACCEPTED" if ok else "REJECTED")
        status = AuthorizationStatus.accepted if ok else AuthorizationStatus.blocked
        return call_result.Authorize(id_tag_info={"status": status})

    @on(Action.start_transaction)
    async def on_start_transaction(self, connector_id, id_tag, meter_start, timestamp, **kwargs):
        if not is_authorized(id_tag):
            return call_result.StartTransaction(
                transaction_id=0, id_tag_info={"status": AuthorizationStatus.blocked}
            )
        txn_id = db.next_transaction_id()
        db.start_session(txn_id, self.id, connector_id, id_tag, meter_start, timestamp)
        log.info("[%s] StartTransaction txn=%s connector=%s id_tag=%s meter_start=%sWh",
                 self.id, txn_id, connector_id, id_tag, meter_start)
        return call_result.StartTransaction(
            transaction_id=txn_id, id_tag_info={"status": AuthorizationStatus.accepted}
        )

    @on(Action.meter_values)
    async def on_meter_values(self, connector_id, meter_value, **kwargs):
        txn_id = kwargs.get("transaction_id")
        for entry in meter_value:
            ts = entry.get("timestamp", now_iso())
            for sv in entry.get("sampled_value", []):
                db.add_meter_value(
                    txn_id, connector_id,
                    sv.get("measurand", "Energy.Active.Import.Register"),
                    sv.get("value"), sv.get("unit"), ts,
                )
                log.info("[%s] MeterValue txn=%s %s=%s%s",
                         self.id, txn_id, sv.get("measurand", "Energy"), sv.get("value"), sv.get("unit") or "")
        return call_result.MeterValues()

    @on(Action.stop_transaction)
    async def on_stop_transaction(self, meter_stop, timestamp, transaction_id, **kwargs):
        kwh = db.stop_session(transaction_id, meter_stop, timestamp, kwargs.get("reason"))
        log.info("[%s] StopTransaction txn=%s meter_stop=%sWh -> %s kWh (billable)",
                 self.id, transaction_id, meter_stop, kwh)
        return call_result.StopTransaction()

    @on(Action.data_transfer)
    async def on_data_transfer(self, vendor_id, **kwargs):
        log.info("[%s] DataTransfer vendor_id=%s %s", self.id, vendor_id, kwargs)
        return call_result.DataTransfer(status="Accepted")


def _requested_path(websocket) -> str:
    """Charge-point id is the URL path. websockets moved .path across versions."""
    try:
        return websocket.request.path  # websockets >= 13
    except AttributeError:
        return getattr(websocket, "path", "/")


async def on_connect(websocket):
    path = _requested_path(websocket)
    charge_point_id = path.strip("/").split("/")[-1] or "unknown"

    if "ocpp1.6" not in (websocket.subprotocol or ""):
        log.warning("Charger %s connected without ocpp1.6 subprotocol (got %r)",
                    charge_point_id, websocket.subprotocol)

    log.info("Charger connected: %s", charge_point_id)
    cp = ChargePoint(charge_point_id, websocket)
    try:
        await cp.start()
    except websockets.exceptions.ConnectionClosed:
        log.info("Charger disconnected: %s", charge_point_id)


async def main():
    db.init_db()
    log.info("CSMS listening on ws://%s:%s  (charger URL: ws://<ip>:%s/<id>)",
             LISTEN_HOST, LISTEN_PORT, LISTEN_PORT)
    async with websockets.serve(on_connect, LISTEN_HOST, LISTEN_PORT, subprotocols=["ocpp1.6"]):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("CSMS stopped.")
