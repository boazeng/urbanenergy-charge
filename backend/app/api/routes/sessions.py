"""Charging sessions — recent transactions (energy, cost, driver, status)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_analytics_service
from app.api.schemas import SessionOut
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("", response_model=list[SessionOut])
async def list_sessions(
    limit: int = Query(50, ge=1, le=500),
    svc: AnalyticsService = Depends(get_analytics_service),
) -> list[SessionOut]:
    return [SessionOut.from_domain(s) for s in await svc.sessions(limit)]
