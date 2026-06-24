from __future__ import annotations

from app.adapters.seed.seed_adapter import SeedAdapter
from app.services.analytics_service import AnalyticsService
from fastapi.testclient import TestClient


def test_summary_contract(client: TestClient) -> None:
    """The dashboard relies on these exact camelCase keys — guard the contract."""
    r = client.get("/api/analytics/summary")
    assert r.status_code == 200
    body = r.json()
    for key in (
        "locations",
        "chargingStations",
        "partners",
        "drivers",
        "totalEnergyKwh",
        "walletBalance",
        "topupCount",
        "totalChargingTransactions",
        "revenue",
        "deltas",
    ):
        assert key in body, f"missing {key}"
    assert body["chargingStations"] == 122


def test_partner_wallet_shape(client: TestClient) -> None:
    r = client.get("/api/partners")
    assert r.status_code == 200
    partners = r.json()
    assert partners and "totalUnsettledAmount" in partners[0]["wallet"]


def test_locations_list(client: TestClient) -> None:
    r = client.get("/api/locations")
    assert r.status_code == 200
    locs = r.json()
    assert len(locs) == 18
    assert {"id", "name", "status", "city", "state", "chargers"} <= locs[0].keys()


def test_sessions_list(client: TestClient) -> None:
    r = client.get("/api/sessions?limit=10")
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 10
    assert {"id", "transactionId", "charger", "kwh", "cost", "status"} <= rows[0].keys()


def test_consumption_days_param(client: TestClient) -> None:
    r = client.get("/api/analytics/consumption?days=5")
    assert r.status_code == 200
    assert len(r.json()) == 5


def test_consumption_rejects_out_of_range(client: TestClient) -> None:
    assert client.get("/api/analytics/consumption?days=0").status_code == 422
    assert client.get("/api/analytics/consumption?days=999").status_code == 422


async def test_service_clamps_days() -> None:
    # Guard the business rule directly, independent of HTTP validation.
    svc = AnalyticsService(SeedAdapter())
    assert len(await svc.consumption(10_000)) == 366
    assert len(await svc.consumption(-5)) == 1


async def test_seed_summary_is_typed() -> None:
    summary = await SeedAdapter().summary()
    assert summary.charging_stations == 122
    assert summary.revenue.count == 50
