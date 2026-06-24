"""Ports — the stable interfaces the core depends on.

`AnalyticsDataSource` is THE seam that makes the Evoltsoft dependency removable.
The services and API know only this interface; concrete adapters (seed today,
Evoltsoft in Phase 1, native CSMS/Priority later) implement it. Deleting the
Evoltsoft integration later = deleting one adapter class, nothing else.

Methods are async so HTTP-backed adapters fit naturally; sync adapters just
return immediately.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

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


class AnalyticsDataSource(ABC):
    """A source of the analytics/operational data shown on the dashboard."""

    name: str = "abstract"

    @abstractmethod
    async def summary(self) -> AnalyticsSummary: ...

    @abstractmethod
    async def evse_status(self) -> EvseStatusCounts: ...

    @abstractmethod
    async def session_status(self) -> SessionStatusCounts: ...

    @abstractmethod
    async def consumption(self, days: int) -> list[ConsumptionPoint]: ...

    @abstractmethod
    async def revenue(self, days: int) -> list[RevenuePoint]: ...

    @abstractmethod
    async def partners(self) -> list[Partner]: ...

    @abstractmethod
    async def locations(self) -> list[Location]: ...

    @abstractmethod
    async def sessions(self, limit: int) -> list[Session]: ...

    async def healthcheck(self) -> bool:
        """Whether this source is reachable. Overridden by remote adapters."""
        return True
