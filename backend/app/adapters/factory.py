"""Adapter factory — picks the configured data source at startup.

This is the single switch that drives the gradual migration. Today it returns
the SeedAdapter; Phase 1 adds the EvoltsoftAdapter; later the NativeAdapter.
Nothing else in the app references concrete adapters.
"""

from __future__ import annotations

import logging

from app.core.config import DataSource, Settings
from app.domain.ports import AnalyticsDataSource

log = logging.getLogger("app.adapters")


def build_data_source(settings: Settings) -> AnalyticsDataSource:
    source = settings.data_source
    log.info("data source selected", extra={"data_source": source.value})

    if source is DataSource.seed:
        from app.adapters.seed.seed_adapter import SeedAdapter

        return SeedAdapter()

    if source is DataSource.evoltsoft:
        from app.adapters.evoltsoft.client import EvoltsoftClient
        from app.adapters.evoltsoft.evoltsoft_adapter import EvoltsoftAdapter

        client = EvoltsoftClient(
            base_url=settings.evoltsoft_base_url,
            firebase_api_key=settings.evoltsoft_firebase_api_key,
            email=settings.evoltsoft_email,
            password=settings.evoltsoft_password,
            timeout_s=settings.evoltsoft_timeout_s,
        )
        return EvoltsoftAdapter(client, business_org_id=settings.evoltsoft_business_org_id)

    # Later: from app.adapters.native.native_adapter import NativeAdapter
    raise NotImplementedError(f"data source '{source.value}' not wired yet")
