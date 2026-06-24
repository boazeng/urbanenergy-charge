"""Liveness & readiness probes — used by the host / monitoring to detect faults."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status

from app.api.deps import get_analytics_service
from app.core.config import get_settings
from app.services.analytics_service import AnalyticsService

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness: the process is up. Cheap, no dependencies."""
    return {"status": "ok", "env": get_settings().env.value}


@router.get("/ready")
async def ready(
    response: Response,
    svc: AnalyticsService = Depends(get_analytics_service),
) -> dict[str, object]:
    """Readiness: upstream data source is reachable. Drives load-balancer health."""
    healthy = await svc.source_healthy()
    if not healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"ready": healthy, "dataSource": get_settings().data_source.value}
