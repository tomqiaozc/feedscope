from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class GroupCreate(BaseModel):
    name: str
    description: str | None = None


class GroupUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class GroupOut(BaseModel):
    id: int
    name: str
    description: str | None = None
    member_count: int = 0
    created_at: datetime
    updated_at: datetime


class GroupMemberCreate(BaseModel):
    username: str
    display_name: str | None = None
    notes: str | None = None


class GroupMemberOut(BaseModel):
    id: int
    username: str
    display_name: str | None = None
    profile_image_url: str | None = None
    notes: str | None = None
    created_at: datetime


class BatchMemberCreate(BaseModel):
    members: list[GroupMemberCreate]


class BatchDeleteRequest(BaseModel):
    member_ids: list[int]


class ProfileOut(BaseModel):
    username: str
    display_name: str | None = None
    description: str | None = None
    profile_image_url: str | None = None
    followers_count: int | None = None
    following_count: int | None = None
    tweet_count: int | None = None
    is_verified: bool | None = None
    location: str | None = None
    website: str | None = None
    joined_at: datetime | None = None


class ProfileRefreshRequest(BaseModel):
    usernames: list[str]
