"""Integration tests for group routes."""

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


def _mock_group(id=1, name="Test Group", description=None):
    return SimpleNamespace(
        id=id,
        name=name,
        description=description,
        created_at=NOW,
        updated_at=NOW,
    )


def _mock_member(id=1, username="user1", group_id=1):
    return SimpleNamespace(
        id=id,
        username=username,
        group_id=group_id,
        display_name=None,
        profile_image_url=None,
        notes=None,
        created_at=NOW,
    )


# --- Group CRUD ---


@patch("app.routes.groups.GroupRepo")
async def test_list_groups(mock_repo_cls, client, auth_headers):
    mock_repo_cls.return_value.list = AsyncMock(
        return_value=[
            {"group": _mock_group(), "member_count": 5},
        ]
    )
    resp = await client.get("/api/v1/groups", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["name"] == "Test Group"
    assert data["data"][0]["member_count"] == 5


@patch("app.routes.groups.GroupRepo")
async def test_create_group(mock_repo_cls, client, auth_headers):
    mock_repo_cls.return_value.create = AsyncMock(return_value=_mock_group(name="New Group"))
    resp = await client.post(
        "/api/v1/groups",
        headers=auth_headers,
        json={"name": "New Group"},
    )
    assert resp.status_code == 201
    assert resp.json()["data"]["name"] == "New Group"


@patch("app.routes.groups.GroupRepo")
async def test_update_group(mock_repo_cls, client, auth_headers):
    mock_repo_cls.return_value.update = AsyncMock(return_value=_mock_group(name="Updated"))
    resp = await client.put(
        "/api/v1/groups/1",
        headers=auth_headers,
        json={"name": "Updated"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == "Updated"


@patch("app.routes.groups.GroupRepo")
async def test_update_group_not_found(mock_repo_cls, client, auth_headers):
    mock_repo_cls.return_value.update = AsyncMock(return_value=None)
    resp = await client.put(
        "/api/v1/groups/999",
        headers=auth_headers,
        json={"name": "X"},
    )
    assert resp.status_code == 404


@patch("app.routes.groups.GroupRepo")
async def test_update_group_empty_body(mock_repo_cls, client, auth_headers):
    resp = await client.put(
        "/api/v1/groups/1",
        headers=auth_headers,
        json={},
    )
    assert resp.status_code == 400


@patch("app.routes.groups.GroupRepo")
async def test_delete_group(mock_repo_cls, client, auth_headers):
    mock_repo_cls.return_value.delete = AsyncMock(return_value=True)
    resp = await client.delete("/api/v1/groups/1", headers=auth_headers)
    assert resp.status_code == 200


@patch("app.routes.groups.GroupRepo")
async def test_delete_group_not_found(mock_repo_cls, client, auth_headers):
    mock_repo_cls.return_value.delete = AsyncMock(return_value=False)
    resp = await client.delete("/api/v1/groups/999", headers=auth_headers)
    assert resp.status_code == 404


# --- Group Members ---


@patch("app.routes.groups.GroupMemberRepo")
async def test_list_group_members(mock_repo_cls, client, auth_headers):
    mock_repo_cls.return_value.list = AsyncMock(return_value=[_mock_member()])
    resp = await client.get("/api/v1/groups/1/members", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 1


@patch("app.routes.groups.GroupMemberRepo")
@patch("app.routes.groups.GroupRepo")
async def test_create_group_member(mock_g_cls, mock_m_cls, client, auth_headers):
    mock_g_cls.return_value.get = AsyncMock(return_value=_mock_group())
    mock_m_cls.return_value.create = AsyncMock(return_value=_mock_member(username="newuser"))
    resp = await client.post(
        "/api/v1/groups/1/members",
        headers=auth_headers,
        json={"username": "newuser"},
    )
    assert resp.status_code == 201
    assert resp.json()["data"]["username"] == "newuser"


@patch("app.routes.groups.GroupMemberRepo")
@patch("app.routes.groups.GroupRepo")
async def test_create_member_group_not_found(mock_g_cls, mock_m_cls, client, auth_headers):
    mock_g_cls.return_value.get = AsyncMock(return_value=None)
    resp = await client.post(
        "/api/v1/groups/999/members",
        headers=auth_headers,
        json={"username": "user1"},
    )
    assert resp.status_code == 404


@patch("app.routes.groups.GroupMemberRepo")
@patch("app.routes.groups.GroupRepo")
async def test_batch_create_members(mock_g_cls, mock_m_cls, client, auth_headers):
    mock_g_cls.return_value.get = AsyncMock(return_value=_mock_group())
    mock_m_cls.return_value.batch_create = AsyncMock(
        return_value=[
            _mock_member(id=1, username="u1"),
            _mock_member(id=2, username="u2"),
        ]
    )
    resp = await client.post(
        "/api/v1/groups/1/members/batch",
        headers=auth_headers,
        json={"members": [{"username": "u1"}, {"username": "u2"}]},
    )
    assert resp.status_code == 201
    assert len(resp.json()["data"]) == 2


@patch("app.routes.groups.GroupMemberRepo")
async def test_batch_delete_members(mock_repo_cls, client, auth_headers):
    mock_repo_cls.return_value.batch_delete = AsyncMock(return_value=2)
    resp = await client.request(
        "DELETE",
        "/api/v1/groups/1/members/batch",
        headers=auth_headers,
        json={"member_ids": [1, 2]},
    )
    assert resp.status_code == 200
    assert resp.json()["deleted"] == 2


@patch("app.routes.groups.GroupMemberRepo")
async def test_delete_single_member(mock_repo_cls, client, auth_headers):
    mock_repo_cls.return_value.get = AsyncMock(return_value=_mock_member(group_id=1))
    mock_repo_cls.return_value.delete = AsyncMock()
    resp = await client.delete("/api/v1/groups/1/members/1", headers=auth_headers)
    assert resp.status_code == 200


@patch("app.routes.groups.GroupMemberRepo")
async def test_delete_member_wrong_group(mock_repo_cls, client, auth_headers):
    mock_repo_cls.return_value.get = AsyncMock(return_value=_mock_member(group_id=99))
    resp = await client.delete("/api/v1/groups/1/members/1", headers=auth_headers)
    assert resp.status_code == 404
