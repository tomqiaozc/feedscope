"""Integration tests for health endpoint."""


async def test_health_returns_200(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


async def test_health_no_auth_required(client):
    # No X-User-Id header needed for health
    resp = await client.get("/health")
    assert resp.status_code == 200
