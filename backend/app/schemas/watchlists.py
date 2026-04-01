from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel

# --- Watchlist ---


class WatchlistCreate(BaseModel):
    name: str
    description: str | None = None


class WatchlistUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class WatchlistOut(BaseModel):
    id: int
    name: str
    description: str | None = None
    member_count: int = 0
    post_count: int = 0
    created_at: datetime
    updated_at: datetime


# --- Member ---


class MemberCreate(BaseModel):
    username: str
    display_name: str | None = None
    notes: str | None = None
    tags: list[str] = []


class MemberUpdate(BaseModel):
    display_name: str | None = None
    notes: str | None = None
    tags: list[str] | None = None


class MemberOut(BaseModel):
    id: int
    username: str
    display_name: str | None = None
    profile_image_url: str | None = None
    notes: str | None = None
    tags: list[str] = []
    created_at: datetime


# --- Post ---


class PostOut(BaseModel):
    id: int
    platform_post_id: str | None = None
    author_username: str | None = None
    content: str | None = None
    post_json: dict | None = None
    metrics: dict | None = None
    media: Any = None
    translation: str | None = None
    editorial: str | None = None
    quoted_translation: str | None = None
    posted_at: datetime | None = None
    fetched_at: datetime | None = None
    translated_at: datetime | None = None


# --- FetchLog ---


class FetchLogOut(BaseModel):
    id: int
    type: str
    status: str
    member_count: int | None = None
    post_count: int | None = None
    error_count: int | None = None
    errors: dict | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


# --- WatchlistSetting ---


class WatchlistSettingOut(BaseModel):
    key: str
    value: str | None = None


class WatchlistSettingUpdate(BaseModel):
    key: str
    value: str
