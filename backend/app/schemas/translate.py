from __future__ import annotations

from pydantic import BaseModel


class TranslateRequest(BaseModel):
    text: str
    quoted_text: str | None = None


class TranslateResponse(BaseModel):
    translation: str
    editorial: str | None = None
    quoted_translation: str | None = None
