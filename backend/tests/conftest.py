"""Shared test fixtures.

Force the seed data source for the whole test session so tests never touch the
live Evoltsoft API, regardless of what `.env` selects. A real environment
variable takes precedence over the `.env` file in pydantic-settings.
"""

from __future__ import annotations

import os

os.environ["UE_DATA_SOURCE"] = "seed"
os.environ["UE_ENV"] = "dev"

from collections.abc import Iterator  # noqa: E402

import pytest  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.main import create_app  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

get_settings.cache_clear()  # drop any settings cached before the env override


@pytest.fixture(scope="session")
def client() -> Iterator[TestClient]:
    # `with` runs the lifespan, which builds the (seed) data source on app.state.
    with TestClient(create_app()) as c:
        yield c
