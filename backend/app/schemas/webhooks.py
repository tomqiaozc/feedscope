from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class WebhookKeyCreate(BaseModel):
    name: str


class WebhookKeyOut(BaseModel):
    id: int
    name: str
    key_prefix: str | None = None
    created_at: datetime
    last_used_at: datetime | None = None


class WebhookKeyCreated(BaseModel):
    id: int
    name: str
    key_prefix: str | None = None
    key: str
    created_at: datetime


class UsageSummary(BaseModel):
    date: str | None = None
    endpoint: str | None = None
    count: int = 0


class UsageEntry(BaseModel):
    id: int
    endpoint: str | None = None
    called_at: datetime
