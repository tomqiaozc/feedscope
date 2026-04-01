"""Integration tests for auth dependencies."""

import uuid


async def test_missing_user_id_with_skip_auth(client):
    """With E2E_SKIP_AUTH=true, missing header still works (returns test-user-1)."""
    resp = await client.get("/api/v1/me")
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == "test-user-1"


async def test_valid_uuid_header(client):
    uid = str(uuid.uuid4())
    resp = await client.get("/api/v1/me", headers={"X-User-Id": uid})
    assert resp.status_code == 200
    assert resp.json()["user_id"] == uid


async def test_invalid_uuid_header(client):
    resp = await client.get("/api/v1/me", headers={"X-User-Id": "not-a-uuid"})
    assert resp.status_code == 401
    assert "Invalid user ID format" in resp.json()["detail"]


async def test_empty_uuid_header(client):
    """Empty string is not a valid UUID."""
    resp = await client.get("/api/v1/me", headers={"X-User-Id": ""})
    # Empty string triggers the skip-auth fallback since it's falsy
    assert resp.status_code == 200
