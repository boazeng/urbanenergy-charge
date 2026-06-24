from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_ok(client: TestClient) -> None:
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_ready_reports_source(client: TestClient) -> None:
    r = client.get("/api/ready")
    assert r.status_code == 200
    body = r.json()
    assert body["ready"] is True
    assert body["dataSource"] == "seed"


def test_request_id_header_present(client: TestClient) -> None:
    r = client.get("/api/health")
    assert r.headers.get("x-request-id")
