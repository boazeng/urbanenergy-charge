"""Analytics service — the application layer between the API and the data source.

Thin today (delegates to the port), but it is the right home for business rules
that must hold regardless of source: caching, aggregation across native +
mirrored data during migration, validation, etc.
"""

from __future__ import annotations

from app.domain.models import (
    AnalyticsSummary,
    ConsumptionPoint,
    EvseStatusCounts,
    Location,
    Partner,
    RevenuePoint,
    Session,
    SessionStatusCounts,
)
from app.domain.ports import AnalyticsDataSource

_MAX_DAYS = 366


class AnalyticsService:
    def __init__(self, source: AnalyticsDataSource) -> None:
        self._source = source

    @staticmethod
    def _clamp_days(days: int) -> int:
        return max(1, min(days, _MAX_DAYS))

    async def summary(self) -> AnalyticsSummary:
        return await self._source.summary()

    async def evse_status(self) -> EvseStatusCounts:
        return await self._source.evse_status()

    async def session_status(self) -> SessionStatusCounts:
        return await self._source.session_status()

    async def consumption(self, days: int) -> list[ConsumptionPoint]:
        return await self._source.consumption(self._clamp_days(days))

    async def revenue(self, days: int) -> list[RevenuePoint]:
        return await self._source.revenue(self._clamp_days(days))

    async def partners(self) -> list[Partner]:
        return await self._source.partners()

    async def locations(self) -> list[Location]:
        return await self._source.locations()

    async def sessions(self, limit: int = 50) -> list[Session]:
        return await self._source.sessions(max(1, min(limit, 500)))

    async def source_healthy(self) -> bool:
        return await self._source.healthcheck()
