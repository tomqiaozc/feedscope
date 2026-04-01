"""Integration tests for watchlist + member routes."""

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


def _mock_watchlist(id=1, name="Test WL", description=None):
    return SimpleNamespace(
        id=id,
        name=name,
        description=description,
        created_at=NOW,
        updated_at=NOW,
    )


def _mock_member(id=1, username="user1", watchlist_id=1):
    return SimpleNamespace(
        id=id,
        username=username,
        watchlist_id=watchlist_id,
        display_name=None,
        profile_image_url=None,
        notes=None,
        tags=[],
        created_at=NOW,
    )


# --- Watchlist CRUD ---


@patch("app.routes.watchlists.WatchlistRepo")
async def test_list_watchlists(mock_repo_cls, client, auth_headers):
    mock_repo_cls.return_value.list_with_counts = AsyncMock(
        return_value=[
            {"watchlist": _mock_watchlist(), "member_count": 3, "post_count": 10},
        ]
    )
    resp = await client.get("/api/v1/watchlists", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert len(data["data"]) == 1
    assert data["data"][0]["name"] == "Test WL"
    assert data["data"][0]["member_count"] == 3


@patch("app.routes.watchlists.WatchlistRepo")
async def test_create_watchlist(mock_repo_cls, client, auth_headers):
    mock_repo_cls.return_value.create = AsyncMock(return_value=_mock_watchlist(name="New WL"))
    resp = await client.post(
        "/api/v1/watchlists",
        headers=auth_headers,
        json={"name": "New WL"},
    )
    assert resp.status_code == 201
    assert resp.json()["data"]["name"] == "New WL"


@patch("app.routes.watchlists.WatchlistRepo")
async def test_update_watchlist(mock_repo_cls, client, auth_headers):
    mock_repo_cls.return_value.update = AsyncMock(return_value=_mock_watchlist(name="Updated"))
    resp = await client.put(
        "/api/v1/watchlists/1",
        headers=auth_headers,
        json={"name": "Updated"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == "Updated"


@patch("app.routes.watchlists.WatchlistRepo")
async def test_update_watchlist_not_found(mock_repo_cls, client, auth_headers):
    mock_repo_cls.return_value.update = AsyncMock(return_value=None)
    resp = await client.put(
        "/api/v1/watchlists/999",
        headers=auth_headers,
        json={"name": "X"},
    )
    assert resp.status_code == 404


@patch("app.routes.watchlists.WatchlistRepo")
async def test_update_watchlist_empty_body(mock_repo_cls, client, auth_headers):
    resp = await client.put(
        "/api/v1/watchlists/1",
        headers=auth_headers,
        json={},
    )
    assert resp.status_code == 400


@patch("app.routes.watchlists.WatchlistRepo")
async def test_delete_watchlist(mock_repo_cls, client, auth_headers):
    mock_repo_cls.return_value.delete = AsyncMock(return_value=True)
    resp = await client.delete("/api/v1/watchlists/1", headers=auth_headers)
    assert resp.status_code == 200


@patch("app.routes.watchlists.WatchlistRepo")
async def test_delete_watchlist_not_found(mock_repo_cls, client, auth_headers):
    mock_repo_cls.return_value.delete = AsyncMock(return_value=False)
    resp = await client.delete("/api/v1/watchlists/999", headers=auth_headers)
    assert resp.status_code == 404


# --- Members ---


@patch("app.routes.watchlists.MemberRepo")
async def test_list_members(mock_repo_cls, client, auth_headers):
    mock_repo_cls.return_value.list = AsyncMock(return_value=[_mock_member()])
    resp = await client.get("/api/v1/watchlists/1/members", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 1


@patch("app.routes.watchlists.MemberRepo")
@patch("app.routes.watchlists.WatchlistRepo")
async def test_create_member(mock_wl_cls, mock_m_cls, client, auth_headers):
    mock_wl_cls.return_value.get = AsyncMock(return_value=_mock_watchlist())
    member = _mock_member(username="newuser")
    mock_m_cls.return_value.create = AsyncMock(return_value=member)
    mock_m_cls.return_value.get = AsyncMock(return_value=member)

    resp = await client.post(
        "/api/v1/watchlists/1/members",
        headers=auth_headers,
        json={"username": "newuser"},
    )
    assert resp.status_code == 201
    assert resp.json()["data"]["username"] == "newuser"


@patch("app.routes.watchlists.MemberRepo")
@patch("app.routes.watchlists.WatchlistRepo")
async def test_create_member_watchlist_not_found(mock_wl_cls, mock_m_cls, client, auth_headers):
    mock_wl_cls.return_value.get = AsyncMock(return_value=None)
    resp = await client.post(
        "/api/v1/watchlists/999/members",
        headers=auth_headers,
        json={"username": "user1"},
    )
    assert resp.status_code == 404


@patch("app.routes.watchlists.MemberRepo")
async def test_delete_member(mock_repo_cls, client, auth_headers):
    mock_repo_cls.return_value.get = AsyncMock(return_value=_mock_member(watchlist_id=1))
    mock_repo_cls.return_value.delete = AsyncMock()
    resp = await client.delete("/api/v1/watchlists/1/members/1", headers=auth_headers)
    assert resp.status_code == 200


@patch("app.routes.watchlists.MemberRepo")
async def test_delete_member_wrong_watchlist(mock_repo_cls, client, auth_headers):
    mock_repo_cls.return_value.get = AsyncMock(return_value=_mock_member(watchlist_id=99))
    resp = await client.delete("/api/v1/watchlists/1/members/1", headers=auth_headers)
    assert resp.status_code == 404
