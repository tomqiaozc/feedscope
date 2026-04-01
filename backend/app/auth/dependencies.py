import uuid

from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.engine import get_db_session


async def get_current_user(request: Request) -> str:
    user_id = request.headers.get("X-User-Id")
    if user_id:
        try:
            uuid.UUID(user_id)
        except ValueError as exc:
            raise HTTPException(status_code=401, detail="Invalid user ID format") from exc
        return user_id
    if settings.effective_e2e_skip_auth:
        return "test-user-1"
    raise HTTPException(status_code=401, detail="Not authenticated")


async def authenticate_webhook_key(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> tuple[str, int]:
    """Authenticate via X-Webhook-Key header. Returns (user_id, webhook_id)."""
    key = request.headers.get("X-Webhook-Key")
    if not key:
        raise HTTPException(status_code=401, detail="Missing X-Webhook-Key header")

    from app.db.repos.webhook_repo import WebhookRepo
    from app.db.repos.webhook_usage_repo import WebhookUsageRepo

    # Use a dummy user_id for the repo since verify() scans all keys
    repo = WebhookRepo("", session)
    result = await repo.verify(key)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid webhook key")

    user_id, webhook_id = result

    # Record usage (fire-and-forget within same transaction)
    usage_repo = WebhookUsageRepo(user_id, session)
    await usage_repo.record(webhook_id, endpoint=request.url.path)

    return user_id, webhook_id
