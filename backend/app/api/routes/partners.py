"""Partner organisations — the settlement view (wallet / unsettled balance)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_analytics_service
from app.api.schemas import PartnerOut
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/partners", tags=["partners"])


@router.get("", response_model=list[PartnerOut])
async def list_partners(
    svc: AnalyticsService = Depends(get_analytics_service),
) -> list[PartnerOut]:
    return [PartnerOut.from_domain(p) for p in await svc.partners()]
