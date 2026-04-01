from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class PostOut(BaseModel):
    platform_post_id: str
    author_username: str | None = None
    author_display_name: str | None = None
    author_profile_image_url: str | None = None
    author_is_verified: bool = False
    content: str
    posted_at: datetime | None = None
    metrics: dict | None = None
    media: Any = None
    quoted_post: PostOut | None = None
    is_retweet: bool = False
    is_reply: bool = False
    language: str | None = None


class UserInfoOut(BaseModel):
    username: str
    display_name: str | None = None
    description: str | None = None
    profile_image_url: str | None = None
    followers_count: int = 0
    following_count: int = 0
    tweet_count: int = 0
    is_verified: bool = False
    location: str | None = None
    website: str | None = None
    joined_at: datetime | None = None
