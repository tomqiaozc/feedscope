"""Integration tests for webhook key routes."""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.db.engine import get_db_session
from app.main import app


def _mock_session():
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture(autouse=True)
def override_db():
    mock_sess = _mock_session()

    async def _override():
        yield mock_sess

    app.dependency_overrides[get_db_session] = _override
    yield mock_sess
    app.dependency_overrides.pop(get_db_session, None)


NOW = datetime.now(UTC)


def _mock_webhook(id=1, name="My Key"):
    return SimpleNamespace(
        id=id,
        name=name,
        key_prefix="fsk_abcd",
        key_hash="abc123",
        last_used_at=None,
        created_at=NOW,
    )


# --- Webhook Key CRUD ---


@patch("app.routes.webhooks.WebhookRepo")
async def test_list_webhook_keys(mock_repo_cls, client, auth_headers):
    mock_repo_cls.return_value.list = AsyncMock(return_value=[_mock_webhook()])
    resp = await client.get("/api/v1/webhooks", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["name"] == "My Key"
    assert data["data"][0]["key_prefix"] == "fsk_abcd"
    # Full key should NOT be in list response
    assert "key" not in data["data"][0] or data["data"][0].get("key") is None


@patch("app.routes.webhooks.WebhookRepo")
async def test_create_webhook_key(mock_repo_cls, client, auth_headers):
    webhook = _mock_webhook(name="New Key")
    full_key = "fsk_abcdefgh12345678"
    mock_repo_cls.return_value.create = AsyncMock(return_value=(webhook, full_key))

    resp = await client.post(
        "/api/v1/webhooks",
        headers=auth_headers,
        json={"name": "New Key"},
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["name"] == "New Key"
    assert data["key"] == full_key  # Full key returned on create


@patch("app.routes.webhooks.WebhookRepo")
async def test_delete_webhook_key(mock_repo_cls, client, auth_headers):
    mock_repo_cls.return_value.delete = AsyncMock(return_value=True)
    resp = await client.delete("/api/v1/webhooks/1", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["success"] is True


@patch("app.routes.webhooks.WebhookRepo")
async def test_delete_webhook_not_found(mock_repo_cls, client, auth_headers):
    mock_repo_cls.return_value.delete = AsyncMock(return_value=False)
    resp = await client.delete("/api/v1/webhooks/999", headers=auth_headers)
    assert resp.status_code == 404


@patch("app.routes.webhooks.WebhookRepo")
async def test_rotate_webhook_key(mock_repo_cls, client, auth_headers):
    webhook = _mock_webhook()
    new_key = "fsk_newkey12345"
    mock_repo_cls.return_value.rotate = AsyncMock(return_value=(webhook, new_key))

    resp = await client.post("/api/v1/webhooks/1/rotate", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["key"] == new_key  # New key returned on rotate


@patch("app.routes.webhooks.WebhookRepo")
async def test_rotate_webhook_not_found(mock_repo_cls, client, auth_headers):
    mock_repo_cls.return_value.rotate = AsyncMock(return_value=None)
    resp = await client.post("/api/v1/webhooks/999/rotate", headers=auth_headers)
    assert resp.status_code == 404


# --- Usage ---


@patch("app.routes.webhooks.WebhookUsageRepo")
async def test_usage_summary(mock_repo_cls, client, auth_headers):
    mock_repo_cls.return_value.get_daily_summary = AsyncMock(
        return_value=[
            {"date": "2024-06-01", "endpoint": "/api/v1/external/search", "count": 15},
        ]
    )
    resp = await client.get("/api/v1/webhooks/usage", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["count"] == 15


@patch("app.routes.webhooks.WebhookUsageRepo")
@patch("app.routes.webhooks.WebhookRepo")
async def test_per_key_usage(mock_wh_cls, mock_u_cls, client, auth_headers):
    mock_wh_cls.return_value.get = AsyncMock(return_value=_mock_webhook())
    mock_u_cls.return_value.get_by_webhook = AsyncMock(
        return_value=[
            SimpleNamespace(id=1, endpoint="/api/v1/external/search", called_at=NOW),
        ]
    )
    resp = await client.get("/api/v1/webhooks/1/usage", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 1


@patch("app.routes.webhooks.WebhookRepo")
async def test_per_key_usage_webhook_not_found(mock_wh_cls, client, auth_headers):
    mock_wh_cls.return_value.get = AsyncMock(return_value=None)
    resp = await client.get("/api/v1/webhooks/999/usage", headers=auth_headers)
    assert resp.status_code == 404


# --- Auth: webhook auth dependency ---


async def test_external_missing_webhook_key(client):
    """External routes require X-Webhook-Key header."""
    resp = await client.get("/api/v1/external/search", params={"q": "test"})
    assert resp.status_code == 401
    assert "Missing X-Webhook-Key" in resp.json()["detail"]


@patch("app.db.repos.webhook_repo.WebhookRepo")
async def test_external_invalid_webhook_key(mock_repo_cls, client, override_db):
    mock_repo_cls.return_value.verify = AsyncMock(return_value=None)
    resp = await client.get(
        "/api/v1/external/search",
        params={"q": "test"},
        headers={"X-Webhook-Key": "fsk_invalid"},
    )
    assert resp.status_code == 401
    assert "Invalid webhook key" in resp.json()["detail"]
