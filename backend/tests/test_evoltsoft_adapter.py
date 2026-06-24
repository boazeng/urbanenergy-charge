"""EvoltsoftAdapter mapping tests.

Drives the adapter against an httpx MockTransport seeded with responses shaped
exactly like the real captured Evoltsoft traffic, and asserts the translation
into our domain models. No network — fully deterministic.
"""

from __future__ import annotations

import httpx
from app.adapters.evoltsoft.client import EvoltsoftClient
from app.adapters.evoltsoft.evoltsoft_adapter import EvoltsoftAdapter

# path -> recorded JSON response (values match the live portal snapshot)
_RESPONSES: dict[str, object] = {
    "/analytics/dashboard/location/count": 18,
    "/analytics/dashboard/chargingStation/count": 122,
    "/analytics/dashboard/partnerOrganisation/count": 17,
    "/analytics/dashboard/evDrivers/count": 221,
    "/analytics/dashboard/user/count": 8,
    "/analytics/dashboard/totalEnergy/consumption": 327952.61,
    "/analytics/dashboard/totalTransactions/charging": 239002.31,
    "/analytics/dashboard/remainingWallet/balance": 202928.80,
    "/analytics/dashboard/topup/count": 803,
    "/analytics/dashboard": [{"revenue": {"transaction_amount": 854.93, "transaction_count": 50}}],
    "/analytics/dashboard/evse/logs": {
        "AVAILABLE": 82,
        "CHARGING": 5,
        "PREPARING": 11,
        "FINISHING": 7,
        "UNKNOWN": 17,
    },
    "/analytics/dashboard/session/logs": {"Running": 5, "Rejected": 34, "Finished": 15738},
    "/analytics/dashboard/consumption/summary": [
        {"date": "2026-06-17", "totalKwh": 1039.02},
        {"date": "2026-06-18", "totalKwh": 921.5},
    ],
    "/analytics/dashboard/revenue": [
        {
            "revenue": {"transaction_amount": 800.0, "transaction_count": 40},
            "created_at": "2026-06-01T21:00:03.923Z",
        },
        {
            "revenue": {"transaction_amount": 854.93, "transaction_count": 50},
            "created_at": "2026-06-02T21:00:03.923Z",
        },
        {"revenue": None, "created_at": "2026-06-03T21:00:03.923Z"},
    ],
    "/portal/partner/organisation/list/all": [
        {
            "id": "Uga08InuVNai1HkRzV3j",
            "name": "משה דיין אשקלון",
            "status": "ACTIVE",
            "address": {"city": "אשקלון"},
            "wallet": {"total_unsettled_amount": 2684.27},
            "charging_station_count": 5,
        }
    ],
}


def _handler(request: httpx.Request) -> httpx.Response:
    body = _RESPONSES.get(request.url.path)
    if body is None:
        return httpx.Response(404, json={"detail": "not found"})
    return httpx.Response(200, json=body)


def _adapter() -> EvoltsoftAdapter:
    mock = httpx.AsyncClient(transport=httpx.MockTransport(_handler), base_url="http://test")
    client = EvoltsoftClient(base_url="http://test", client=mock)
    return EvoltsoftAdapter(client, business_org_id="ORG123")


async def test_summary_maps_counts_and_revenue() -> None:
    s = await _adapter().summary()
    assert s.locations == 18
    assert s.charging_stations == 122
    assert s.partners == 17
    assert s.drivers == 221
    assert s.total_energy_kwh == 327952.61
    assert s.wallet_balance == 202928.80
    assert s.topup_count == 803
    assert s.revenue.amount == 854.93
    assert s.revenue.count == 50


async def test_evse_and_session_status() -> None:
    a = _adapter()
    assert (await a.evse_status())["AVAILABLE"] == 82
    assert (await a.session_status())["Finished"] == 15738


async def test_consumption_and_revenue_series() -> None:
    a = _adapter()
    cons = await a.consumption(7)
    assert len(cons) == 2
    assert cons[0].total_kwh == 1039.02
    rev = await a.revenue(30)
    assert len(rev) == 3
    assert rev[1].revenue == 854.93  # dict revenue -> transaction_amount
    assert rev[2].revenue == 0.0  # null revenue coerced to 0


async def test_partners_mapping() -> None:
    partners = await _adapter().partners()
    assert len(partners) == 1
    p = partners[0]
    assert p.name == "משה דיין אשקלון"
    assert p.city == "אשקלון"
    assert p.unsettled_amount == 2684.27
    assert p.chargers == 5


async def test_healthcheck_true_when_reachable() -> None:
    assert await _adapter().healthcheck() is True


async def test_metric_degrades_on_error() -> None:
    # An endpoint returning 404 must not crash summary — it degrades to 0.
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/analytics/dashboard/location/count":
            return httpx.Response(500, json={})
        return _handler(request)

    mock = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://test")
    adapter = EvoltsoftAdapter(EvoltsoftClient(base_url="http://test", client=mock))
    s = await adapter.summary()
    assert s.locations == 0  # failed metric degraded gracefully
    assert s.charging_stations == 122  # others unaffected
