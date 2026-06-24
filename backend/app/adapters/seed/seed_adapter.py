"""SeedAdapter — a deterministic, in-memory implementation of AnalyticsDataSource.

Used for local development and tests. Figures mirror the real Urban Energy
(Evoltsoft) portal snapshot so the UI looks real. In Phase 1 this is swapped
for the Evoltsoft adapter via configuration — no route or service changes.
"""

from __future__ import annotations

import random
from datetime import UTC, date, datetime, timedelta

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

_CITIES = [
    "אשקלון",
    "תל אביב",
    "חיפה",
    "באר שבע",
    "נתניה",
    "רעננה",
    "הרצליה",
    "ראשון לציון",
    "פתח תקווה",
    "אשדוד",
    "מודיעין",
    "כפר סבא",
    "ירושלים",
    "רחובות",
    "חולון",
    "רמת גן",
    "עפולה",
]
_STREETS = [
    "משה דיין",
    "הרצל",
    "ויצמן",
    "בן גוריון",
    "ז'בוטינסקי",
    "רוטשילד",
    "החשמונאים",
    "הנשיא",
    "סוקולוב",
    "ביאליק",
]

# A reference "today" so the seed is stable across runs (no wall-clock).
_TODAY = date(2026, 6, 23)


class SeedAdapter(AnalyticsDataSource):
    name = "seed"

    def __init__(self) -> None:
        self._rng = random.Random(42)
        self._partners = self._build_partners()

    def _build_partners(self) -> list[Partner]:
        partners: list[Partner] = []
        for i in range(17):
            city = _CITIES[i % len(_CITIES)]
            street = self._rng.choice(_STREETS)
            partners.append(
                Partner(
                    id=f"PRT{i + 1:04d}",
                    name=f"{street} {city}",
                    status="ACTIVE" if self._rng.random() > 0.08 else "INACTIVE",
                    city=city,
                    chargers=self._rng.randint(2, 16),
                    unsettled_amount=round(self._rng.uniform(120, 6500), 2),
                )
            )
        partners[0].unsettled_amount = 2684.27
        return partners

    async def summary(self) -> AnalyticsSummary:
        return AnalyticsSummary(
            locations=18,
            charging_stations=122,
            partners=17,
            drivers=221,
            portal_users=8,
            total_energy_kwh=327952.61,
            total_charging_transactions=239002.31,
            wallet_balance=202928.80,
            topup_count=803,
            revenue=RevenueSnapshot(amount=854.93, count=50),
            deltas={
                "charging_stations": 3.4,
                "drivers": 6.2,
                "total_energy_kwh": 4.1,
                "wallet_balance": -1.8,
                "topup_count": 5.0,
                "total_charging_transactions": 2.7,
            },
        )

    async def evse_status(self) -> EvseStatusCounts:
        return {"AVAILABLE": 82, "CHARGING": 5, "PREPARING": 11, "FINISHING": 7, "UNKNOWN": 17}

    async def session_status(self) -> SessionStatusCounts:
        return {"Running": 5, "Rejected": 34, "Finished": 15738}

    async def consumption(self, days: int) -> list[ConsumptionPoint]:
        rng = random.Random(7)
        out: list[ConsumptionPoint] = []
        for k in range(days - 1, -1, -1):
            d = _TODAY - timedelta(days=k)
            weekend = d.weekday() in (4, 5)
            kwh = 1000 * (0.6 if weekend else 1.0) * rng.uniform(0.85, 1.25)
            out.append(ConsumptionPoint(day=d, total_kwh=round(kwh, 2)))
        return out

    async def revenue(self, days: int) -> list[RevenuePoint]:
        rng = random.Random(11)
        out: list[RevenuePoint] = []
        for k in range(days - 1, -1, -1):
            d = _TODAY - timedelta(days=k)
            weekend = d.weekday() in (4, 5)
            amount = (820 if not weekend else 480) * rng.uniform(0.8, 1.3)
            out.append(RevenuePoint(day=d, revenue=round(amount, 2)))
        return out

    async def partners(self) -> list[Partner]:
        return list(self._partners)

    async def locations(self) -> list[Location]:
        rng = random.Random(99)
        out: list[Location] = []
        for i in range(18):
            city = _CITIES[i % len(_CITIES)]
            out.append(
                Location(
                    id=f"LOC{i + 1:04d}",
                    name=f"{rng.choice(_STREETS)} {city}",
                    status="ACTIVE" if rng.random() > 0.1 else "INACTIVE",
                    city=city,
                    state="מחוז המרכז",
                    chargers=rng.randint(1, 12),
                )
            )
        return out

    async def sessions(self, limit: int) -> list[Session]:
        rng = random.Random(123)
        chargers = ["דוד וענונו", "ALS1474-1", "משה דיין", "רום העיר", "עין הקורא"]
        statuses = ["Finished", "Finished", "Finished", "Running", "Rejected"]
        out: list[Session] = []
        for i in range(min(limit, 40)):
            kwh = round(rng.uniform(0, 42), 2)
            out.append(
                Session(
                    id=f"SES{i + 1:05d}",
                    transaction_id=15800 - i,
                    charger=rng.choice(chargers),
                    driver=f"IL-URB-{rng.randint(10000, 99999)}",
                    status=rng.choice(statuses),
                    kwh=kwh,
                    cost=round(kwh * 0.65, 2),
                    currency="ILS",
                    started_at=datetime(2026, 6, 24, 20, 0, 0, tzinfo=UTC),
                    duration_s=rng.randint(30, 7200),
                )
            )
        return out
