"""Shared pytest fixtures for backend test suite."""

from __future__ import annotations

import os
import uuid

# Force E2E_SKIP_AUTH before importing the app
os.environ["E2E_SKIP_AUTH"] = "true"
os.environ["MOCK_PROVIDER"] = "true"

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

TEST_USER_ID = str(uuid.UUID("00000000-0000-0000-0000-000000000001"))


@pytest.fixture
def test_user_id() -> str:
    return TEST_USER_ID


@pytest.fixture
async def client():
    """Async HTTP client hitting the FastAPI app in-process."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """Headers with a valid test user UUID."""
    return {"X-User-Id": TEST_USER_ID}
