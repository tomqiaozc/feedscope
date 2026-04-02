"""Dashboard aggregation endpoint.

Returns all data needed by the frontend dashboard in a single response,
eliminating 6 separate proxy + auth round trips.
"""

from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.db.engine import get_db_session
from app.db.repos.credentials_repo import CredentialsRepo
from app.db.repos.group_repo import GroupRepo
from app.db.repos.settings_repo import SettingsRepo
from app.db.repos.usage_daily_repo import UsageDailyRepo
from app.db.repos.watchlist_repo import WatchlistRepo
from app.providers.factory import create_provider_for_user

router = APIRouter(prefix="/api/v1", tags=["dashboard"])


@router.get("/dashboard")
async def get_dashboard(
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    creds_repo = CredentialsRepo(user_id, session)
    settings_repo = SettingsRepo(user_id, session)
    usage_repo = UsageDailyRepo(user_id, session)
    group_repo = GroupRepo(user_id, session)
    watchlist_repo = WatchlistRepo(user_id, session)

    creds = await creds_repo.list()
    ai_values = await settings_repo.get_many("ai.")
    watchlists = await watchlist_repo.list()
    # GroupRepo.list() returns list[dict] with {"group": Group, "member_count": int}
    group_rows = await group_repo.list()

    date_to = date.today()
    date_from = date_to - timedelta(days=7)
    usage_rows = await usage_repo.get_summary(date_from=date_from, date_to=date_to)

    credits_data = {"remaining": 0, "total": 0, "reset_at": None}
    try:
        provider = await create_provider_for_user(user_id, session)
        if provider:
            balance = await provider.fetch_credits()
            credits_data = {
                "remaining": balance.remaining,
                "total": balance.total,
                "reset_at": balance.reset_at.isoformat() if balance.reset_at else None,
            }
    except Exception:
        pass  # credits are non-critical

    return {
        "success": True,
        "data": {
            "credentials": [
                {
                    "provider": c.provider,
                    "has_api_key": c.api_key is not None and c.api_key != "",
                    "has_cookie": c.cookie is not None and c.cookie != "",
                }
                for c in creds
            ],
            "ai": {
                "provider_id": ai_values.get("ai.provider_id"),
                "has_api_key": bool(ai_values.get("ai.api_key")),
                "model": ai_values.get("ai.model"),
            },
            "watchlists": [
                {"id": w.id, "name": w.name, "description": w.description} for w in watchlists
            ],
            "groups": [
                {
                    "id": row["group"].id,
                    "name": row["group"].name,
                    "description": row["group"].description,
                }
                for row in group_rows
            ],
            "usage": [
                {"date": str(r.date), "endpoint": r.endpoint, "count": r.count} for r in usage_rows
            ],
            "credits": credits_data,
        },
    }
