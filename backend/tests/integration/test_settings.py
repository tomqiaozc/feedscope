"""Integration tests for settings + credentials routes."""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.db.engine import get_db_session
from app.main import app


def _mock_session():
    """Create a mock async session."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture(autouse=True)
def override_db():
    """Override DB session with mock for all tests in this module."""
    mock_sess = _mock_session()

    async def _override():
        yield mock_sess

    app.dependency_overrides[get_db_session] = _override
    yield mock_sess
    app.dependency_overrides.pop(get_db_session, None)


# --- Credentials ---


@patch("app.routes.settings.CredentialsRepo")
async def test_list_credentials_empty(mock_repo_cls, client, auth_headers):
    mock_repo_cls.return_value.list = AsyncMock(return_value=[])
    resp = await client.get("/api/v1/settings/credentials", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"] == []


@patch("app.routes.settings.CredentialsRepo")
async def test_upsert_credential(mock_repo_cls, client, auth_headers):
    now = datetime.now(UTC)
    mock_cred = SimpleNamespace(
        id=1,
        provider="tweapi",
        api_key="key123",
        cookie=None,
        created_at=now,
        updated_at=now,
    )
    mock_repo_cls.return_value.upsert = AsyncMock(return_value=mock_cred)

    resp = await client.put(
        "/api/v1/settings/credentials",
        headers=auth_headers,
        json={"provider": "tweapi", "api_key": "key123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["provider"] == "tweapi"
    assert data["data"]["has_api_key"] is True
    assert data["data"]["has_cookie"] is False


@patch("app.routes.settings.CredentialsRepo")
async def test_delete_credential_not_found(mock_repo_cls, client, auth_headers):
    mock_repo_cls.return_value.delete = AsyncMock(return_value=False)
    resp = await client.delete("/api/v1/settings/credentials/tweapi", headers=auth_headers)
    assert resp.status_code == 404


@patch("app.routes.settings.CredentialsRepo")
async def test_delete_credential_success(mock_repo_cls, client, auth_headers):
    mock_repo_cls.return_value.delete = AsyncMock(return_value=True)
    resp = await client.delete("/api/v1/settings/credentials/tweapi", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["success"] is True


# --- AI Settings ---


@patch("app.routes.settings.SettingsRepo")
async def test_get_ai_settings(mock_repo_cls, client, auth_headers):
    mock_repo_cls.return_value.get_many = AsyncMock(
        return_value={
            "ai.provider_id": "openai",
            "ai.api_key": "sk-123",
            "ai.model": "gpt-4o-mini",
        }
    )
    resp = await client.get("/api/v1/settings/ai", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["provider_id"] == "openai"
    assert data["has_api_key"] is True
    assert data["model"] == "gpt-4o-mini"


@patch("app.routes.settings.SettingsRepo")
async def test_update_ai_settings(mock_repo_cls, client, auth_headers):
    mock_repo = mock_repo_cls.return_value
    mock_repo.set = AsyncMock()
    mock_repo.get_many = AsyncMock(
        return_value={
            "ai.provider_id": "anthropic",
            "ai.api_key": "sk-ant-123",
            "ai.model": "claude-sonnet-4-20250514",
        }
    )

    resp = await client.put(
        "/api/v1/settings/ai",
        headers=auth_headers,
        json={
            "provider_id": "anthropic",
            "api_key": "sk-ant-123",
            "model": "claude-sonnet-4-20250514",
        },
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["provider_id"] == "anthropic"


@patch("app.routes.settings.SettingsRepo")
async def test_get_ai_settings_empty(mock_repo_cls, client, auth_headers):
    mock_repo_cls.return_value.get_many = AsyncMock(return_value={})
    resp = await client.get("/api/v1/settings/ai", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["has_api_key"] is False
    assert data["provider_id"] is None
