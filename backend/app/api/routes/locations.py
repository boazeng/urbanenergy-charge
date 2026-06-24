"""Locations (sites) — list of physical charging sites."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_analytics_service
from app.api.schemas import LocationOut
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("", response_model=list[LocationOut])
async def list_locations(
    svc: AnalyticsService = Depends(get_analytics_service),
) -> list[LocationOut]:
    return [LocationOut.from_domain(loc) for loc in await svc.locations()]
