"""Fake charge point — pretends to be a real charger so you can test the CSMS
without hardware. It runs a full session: boot -> authorize -> start ->
meter values -> stop, exactly like an OCPP 1.6 charger would.

Run the CSMS first (python central_system.py), then:  python simulate_charger.py
"""
import asyncio
import logging
from datetime import datetime, timezone

import websockets
from ocpp.v16 import ChargePoint as BaseChargePoint
from ocpp.v16 import call

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("sim")

CSMS_URL = "ws://localhost:9000"
CP_ID = "SIM-CP-01"
ID_TAG = "TEST-TAG-1"


def now_iso():
    return datetime.now(timezone.utc).isoformat()


class ChargePoint(BaseChargePoint):
    async def run_session(self):
        await self.call(call.BootNotification(charge_point_vendor="UrbanEnergy",
                                              charge_point_model="POC-Simulator"))
        await self.call(call.StatusNotification(connector_id=1, error_code="NoError", status="Available"))
        await self.call(call.Authorize(id_tag=ID_TAG))

        meter_start = 10000  # Wh
        resp = await self.call(call.StartTransaction(
            connector_id=1, id_tag=ID_TAG, meter_start=meter_start, timestamp=now_iso()))
        txn = resp.transaction_id
        log.info("Session started, transaction_id=%s", txn)

        # Simulate charging: report rising energy every second for ~5 seconds
        energy = meter_start
        for _ in range(5):
            await asyncio.sleep(1)
            energy += 1500  # +1.5 kWh per tick
            await self.call(call.MeterValues(connector_id=1, transaction_id=txn, meter_value=[{
                "timestamp": now_iso(),
                "sampled_value": [{
                    "value": str(energy), "measurand": "Energy.Active.Import.Register", "unit": "Wh"
                }],
            }]))

        await self.call(call.StopTransaction(
            meter_stop=energy, timestamp=now_iso(), transaction_id=txn, reason="Local"))
        log.info("Session stopped. Total = %.3f kWh", (energy - meter_start) / 1000)


async def main():
    async with websockets.connect(f"{CSMS_URL}/{CP_ID}", subprotocols=["ocpp1.6"]) as ws:
        cp = ChargePoint(CP_ID, ws)
        await asyncio.gather(cp.start(), cp.run_session())


if __name__ == "__main__":
    asyncio.run(main())
