"""Analytics endpoints — the data behind the dashboard's KPI cards and charts."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_analytics_service
from app.api.schemas import ConsumptionOut, RevenuePointOut, SummaryOut
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=SummaryOut)
async def summary(svc: AnalyticsService = Depends(get_analytics_service)) -> SummaryOut:
    return SummaryOut.from_domain(await svc.summary())


@router.get("/evse-status")
async def evse_status(svc: AnalyticsService = Depends(get_analytics_service)) -> dict[str, int]:
    return await svc.evse_status()


@router.get("/session-status")
async def session_status(svc: AnalyticsService = Depends(get_analytics_service)) -> dict[str, int]:
    return await svc.session_status()


@router.get("/consumption", response_model=list[ConsumptionOut])
async def consumption(
    days: int = Query(7, ge=1, le=366),
    svc: AnalyticsService = Depends(get_analytics_service),
) -> list[ConsumptionOut]:
    return [ConsumptionOut.from_domain(p) for p in await svc.consumption(days)]


@router.get("/revenue", response_model=list[RevenuePointOut])
async def revenue(
    days: int = Query(30, ge=1, le=366),
    svc: AnalyticsService = Depends(get_analytics_service),
) -> list[RevenuePointOut]:
    return [RevenuePointOut.from_domain(p) for p in await svc.revenue(days)]
