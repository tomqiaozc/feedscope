from datetime import datetime

from pydantic import BaseModel

# --- Credentials ---


class CredentialOut(BaseModel):
    id: int
    provider: str
    has_api_key: bool
    has_cookie: bool
    created_at: datetime
    updated_at: datetime


class CredentialUpsert(BaseModel):
    provider: str
    api_key: str | None = None
    cookie: str | None = None


# --- AI Settings ---


class AISettingsOut(BaseModel):
    provider_id: str | None = None
    has_api_key: bool = False
    model: str | None = None
    base_url: str | None = None
    sdk_type: str | None = None
    custom_prompt: str | None = None


class AISettingsUpdate(BaseModel):
    provider_id: str | None = None
    api_key: str | None = None
    model: str | None = None
    base_url: str | None = None
    sdk_type: str | None = None
    custom_prompt: str | None = None


class AITestResult(BaseModel):
    provider: str | None = None
    model: str | None = None
    response_preview: str | None = None
