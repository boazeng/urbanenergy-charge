"""EvoltsoftAdapter — the removable mirror of the Urban Energy vendor API.

Implements the AnalyticsDataSource port by calling the Evoltsoft Cloud Functions
(mapped from captured traffic) and translating their responses into our domain
models. This is the ONE module that knows the vendor's API; deleting this folder
(and the UE_EVOLTSOFT_* env) removes the dependency entirely.

Resilience: each metric call is isolated — a single failing endpoint degrades to
a default value (logged) instead of breaking the whole dashboard.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, date, datetime, timedelta
from typing import Any

from app.adapters.evoltsoft.client import EvoltsoftClient, EvoltsoftError
from app.domain.models import (
    AnalyticsSummary,
    ConsumptionPoint,
    EvseStatusCounts,
    Location,
    Partner,
    RevenuePoint,
    RevenueSnapshot,
    Session,
    SessionStatusCounts,
)
from app.domain.ports import AnalyticsDataSource

log = logging.getLogger("app.adapters.evoltsoft")


def _now() -> datetime:
    return datetime.now(UTC)


def _parse_date(value: str | None) -> date | None:
    dt = _parse_dt(value)
    return dt.date() if dt else None


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


class EvoltsoftAdapter(AnalyticsDataSource):
    name = "evoltsoft"

    def __init__(self, client: EvoltsoftClient, business_org_id: str = "") -> None:
        self._client = client
        self._org_id = business_org_id

    # --- request-body helpers ---
    # Verified live: the analytics count/value endpoints reject org/squashed/
    # created_at filters (they return 0 or HTTP 500). An empty condition yields
    # the correct global figures, which equal this single-org account's figures.
    def _partner_list_conditions(self) -> list[dict[str, Any]]:
        """The portal partner-list endpoint DOES accept scoping conditions."""
        conds: list[dict[str, Any]] = [{"key": "squashed", "clause": "==", "value": False}]
        if self._org_id:
            conds.append({"key": "business_organisation_id", "clause": "==", "value": self._org_id})
        return conds

    @staticmethod
    def _range_filter(days: int) -> str:
        end = _now()
        start = end - timedelta(days=max(days - 1, 0))
        return f"{start.date().isoformat()}T00:00:00Z to {end.date().isoformat()}T23:59:59Z"

    @staticmethod
    def _revenue_amount(value: Any) -> float:
        """Revenue may arrive as a {transaction_amount,...} object, a number, or null."""
        if isinstance(value, dict):
            return float(value.get("transaction_amount", 0.0))
        if isinstance(value, int | float):
            return float(value)
        return 0.0

    async def _num(self, path: str, default: float = 0.0) -> float:
        """POST an analytics count/value endpoint (empty condition); degrade to `default`."""
        try:
            value = await self._client.post(path, {"condition": []})
            return float(value)
        except (EvoltsoftError, TypeError, ValueError) as exc:
            log.warning("metric failed", extra={"path": path, "error": str(exc)})
            return default

    async def _get(self, method: str, path: str, payload: dict[str, Any], default: Any) -> Any:
        """Fetch raw JSON; degrade to `default` on any Evoltsoft failure (never crash)."""
        try:
            if method == "PUT":
                return await self._client.put(path, payload)
            return await self._client.post(path, payload)
        except EvoltsoftError as exc:
            log.warning("fetch failed", extra={"path": path, "error": str(exc)})
            return default

    # --- AnalyticsDataSource implementation ---
    async def summary(self) -> AnalyticsSummary:
        # Run the revenue snapshot concurrently with the numeric metrics, but
        # gather the numerics separately so they share one type (float).
        revenue_task = asyncio.ensure_future(self._latest_revenue())
        nums = await asyncio.gather(
            self._num("/analytics/dashboard/location/count"),
            self._num("/analytics/dashboard/chargingStation/count"),
            self._num("/analytics/dashboard/partnerOrganisation/count"),
            self._num("/analytics/dashboard/evDrivers/count"),
            self._num("/analytics/dashboard/user/count"),
            self._num("/analytics/dashboard/totalEnergy/consumption"),
            self._num("/analytics/dashboard/totalTransactions/charging"),
            self._num("/analytics/dashboard/remainingWallet/balance"),
            self._num("/analytics/dashboard/topup/count"),
        )
        locations, stations, partners, drivers, users, energy, transactions, wallet, topups = nums
        revenue = await revenue_task
        return AnalyticsSummary(
            locations=int(locations),
            charging_stations=int(stations),
            partners=int(partners),
            drivers=int(drivers),
            portal_users=int(users),
            total_energy_kwh=round(energy, 2),
            total_charging_transactions=round(transactions, 2),
            wallet_balance=round(wallet, 2),
            topup_count=int(topups),
            revenue=revenue,
            deltas={},  # real week-over-week deltas come in a later phase
        )

    async def _latest_revenue(self) -> RevenueSnapshot:
        """Most recent day's revenue, taken from the daily revenue series."""
        rows = await self._get(
            "PUT",
            "/analytics/dashboard/revenue",
            {"payload": {"filter": self._range_filter(3)}},
            [],
        )
        for row in reversed(rows or []):
            rev = row.get("revenue")
            if isinstance(rev, dict):
                return RevenueSnapshot(
                    amount=float(rev.get("transaction_amount", 0.0)),
                    count=int(rev.get("transaction_count", 0)),
                )
        return RevenueSnapshot()

    async def evse_status(self) -> EvseStatusCounts:
        data = await self._get("POST", "/analytics/dashboard/evse/logs", {"condition": []}, {})
        return {str(k): int(v) for k, v in dict(data).items()}

    async def session_status(self) -> SessionStatusCounts:
        data = await self._get("POST", "/analytics/dashboard/session/logs", {"condition": []}, {})
        return {str(k): int(v) for k, v in dict(data).items()}

    async def consumption(self, days: int) -> list[ConsumptionPoint]:
        rows = await self._get(
            "POST",
            "/analytics/dashboard/consumption/summary",
            {"filter": self._range_filter(days), "condition": []},
            [],
        )
        out: list[ConsumptionPoint] = []
        for row in rows or []:
            day = _parse_date(row.get("date"))
            if day is not None:
                out.append(ConsumptionPoint(day=day, total_kwh=float(row.get("totalKwh", 0.0))))
        return out

    async def revenue(self, days: int) -> list[RevenuePoint]:
        rows = await self._get(
            "PUT",
            "/analytics/dashboard/revenue",
            {"payload": {"filter": self._range_filter(days)}},
            [],
        )
        out: list[RevenuePoint] = []
        for row in rows or []:
            day = _parse_date(row.get("created_at") or row.get("timestamp"))
            if day is not None:
                out.append(RevenuePoint(day=day, revenue=self._revenue_amount(row.get("revenue"))))
        return out

    async def partners(self) -> list[Partner]:
        body = {
            "conditions": self._partner_list_conditions(),
            "limit": 0,
            "offset": 0,
            "orderByField": "created_at",
            "direction": "desc",
        }
        rows = await self._get("POST", "/portal/partner/organisation/list/all", body, [])
        out: list[Partner] = []
        for row in rows or []:
            address = row.get("address") or {}
            wallet = row.get("wallet") or {}
            out.append(
                Partner(
                    id=str(row.get("id", "")),
                    name=str(row.get("name", "")),
                    status=str(row.get("status", "")),
                    city=str(address.get("city", "")),
                    chargers=int(row.get("charging_station_count", 0)),
                    unsettled_amount=float(wallet.get("total_unsettled_amount", 0.0)),
                )
            )
        return out

    async def locations(self) -> list[Location]:
        body = {
            "conditions": [],  # org/squashed filters 500 here; empty returns all
            "limit": 0,
            "offset": 0,
            "orderByField": "created_at",
            "direction": "desc",
        }
        rows = await self._get("POST", "/portal/location/list/all", body, [])
        out: list[Location] = []
        for row in rows or []:
            evse = row.get("evse_details") or []
            out.append(
                Location(
                    id=str(row.get("id", "")),
                    name=str(row.get("name", "")),
                    status=str(row.get("status", "")),
                    city=str(row.get("city", "")),
                    state=str(row.get("state", "")),
                    chargers=len(evse) if isinstance(evse, list) else 0,
                )
            )
        return out

    async def sessions(self, limit: int) -> list[Session]:
        body = {
            "conditions": [],
            "limit": limit,
            "offset": 0,
            "orderByField": "updated_at",
            "direction": "desc",
        }
        # This endpoint wraps the list in {"data": [...]}.
        payload = await self._get("POST", "/portal/session/all", body, {})
        rows = payload.get("data", []) if isinstance(payload, dict) else (payload or [])
        out: list[Session] = []
        for row in rows:
            token = row.get("cdr_token") or {}
            cost = row.get("total_cost") or {}
            out.append(
                Session(
                    id=str(row.get("id", "")),
                    transaction_id=int(row.get("transaction_id", 0) or 0),
                    charger=str(row.get("evse_name") or row.get("evse_uid", "")),
                    driver=str(token.get("contract_id") or token.get("uid", "")),
                    status=str(row.get("status", "")),
                    kwh=float(row.get("kwh", 0.0) or 0.0),
                    cost=float(cost.get("incl_vat", 0.0) or 0.0),
                    currency=str(row.get("currency", "")),
                    started_at=_parse_dt(row.get("start_date_time")),
                    duration_s=int(row.get("duration", 0) or 0),
                )
            )
        return out

    async def healthcheck(self) -> bool:
        try:
            await self._client.post("/analytics/dashboard/evDrivers/count", {"condition": []})
            return True
        except EvoltsoftError:
            return False
