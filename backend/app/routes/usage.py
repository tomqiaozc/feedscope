from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.db.engine import get_db_session
from app.db.repos.usage_daily_repo import UsageDailyRepo
from app.providers.factory import create_provider_for_user

router = APIRouter(prefix="/api/v1", tags=["usage"])


@router.get("/usage")
async def get_usage_summary(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    repo = UsageDailyRepo(user_id, session)
    rows = await repo.get_summary(date_from=date_from, date_to=date_to)
    return {
        "success": True,
        "data": [
            {
                "date": str(r.date),
                "endpoint": r.endpoint,
                "count": r.count,
            }
            for r in rows
        ],
    }


@router.get("/credits")
async def get_credits(
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    provider = await create_provider_for_user(user_id, session)
    if not provider:
        return JSONResponse(
            status_code=503,
            content={"success": False, "error": "No Twitter credentials configured."},
        )
    balance = await provider.fetch_credits()
    return {
        "success": True,
        "data": {
            "remaining": balance.remaining,
            "total": balance.total,
            "reset_at": balance.reset_at.isoformat() if balance.reset_at else None,
        },
    }
