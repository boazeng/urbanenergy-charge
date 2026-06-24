"""Dependency injection wiring for the API layer.

The data source is built once at startup (see main.lifespan) and stored on
app.state; the service is a thin per-request wrapper around it.
"""

from __future__ import annotations

from fastapi import Request

from app.domain.ports import AnalyticsDataSource
from app.services.analytics_service import AnalyticsService


def get_data_source(request: Request) -> AnalyticsDataSource:
    return request.app.state.data_source  # type: ignore[no-any-return]


def get_analytics_service(request: Request) -> AnalyticsService:
    return AnalyticsService(get_data_source(request))
