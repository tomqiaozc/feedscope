from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.db.engine import get_db_session
from app.schemas.translate import TranslateRequest, TranslateResponse
from app.services.translation import load_ai_config, translate_post

router = APIRouter(prefix="/api/v1/translate", tags=["translate"])


@router.post("")
async def translate_text(
    body: TranslateRequest,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    if not body.text.strip():
        raise HTTPException(status_code=400, detail="Text is required")

    config = await load_ai_config(user_id, session)
    if not config:
        raise HTTPException(
            status_code=503, detail="No AI provider configured. Add an API key in Settings."
        )

    try:
        result = await translate_post(
            body.text,
            config,
            quoted_content=body.quoted_text,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI translation failed: {exc}") from exc

    return {
        "success": True,
        "data": TranslateResponse(
            translation=result.translation,
            editorial=result.editorial,
            quoted_translation=result.quoted_translation,
        ),
    }
