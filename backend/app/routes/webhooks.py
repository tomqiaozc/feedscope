from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.db.engine import get_db_session
from app.db.repos.webhook_repo import WebhookRepo
from app.db.repos.webhook_usage_repo import WebhookUsageRepo
from app.schemas.webhooks import (
    UsageEntry,
    UsageSummary,
    WebhookKeyCreate,
    WebhookKeyCreated,
    WebhookKeyOut,
)

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


# ---- Webhook Key CRUD ----


@router.get("")
async def list_webhook_keys(
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    repo = WebhookRepo(user_id, session)
    keys = await repo.list()
    return {
        "success": True,
        "data": [
            WebhookKeyOut(
                id=k.id,
                name=k.name,
                key_prefix=k.key_prefix,
                created_at=k.created_at,
                last_used_at=k.last_used_at,
            )
            for k in keys
        ],
    }


@router.post("", status_code=201)
async def create_webhook_key(
    body: WebhookKeyCreate,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    repo = WebhookRepo(user_id, session)
    webhook, full_key = await repo.create(name=body.name)
    return {
        "success": True,
        "data": WebhookKeyCreated(
            id=webhook.id,
            name=webhook.name,
            key_prefix=webhook.key_prefix,
            key=full_key,
            created_at=webhook.created_at,
        ),
    }


@router.delete("/{webhook_id}")
async def delete_webhook_key(
    webhook_id: int,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    repo = WebhookRepo(user_id, session)
    deleted = await repo.delete(webhook_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Webhook key not found")
    return {"success": True}


@router.post("/{webhook_id}/rotate")
async def rotate_webhook_key(
    webhook_id: int,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    repo = WebhookRepo(user_id, session)
    result = await repo.rotate(webhook_id)
    if not result:
        raise HTTPException(status_code=404, detail="Webhook key not found")
    webhook, full_key = result
    return {
        "success": True,
        "data": WebhookKeyCreated(
            id=webhook.id,
            name=webhook.name,
            key_prefix=webhook.key_prefix,
            key=full_key,
            created_at=webhook.created_at,
        ),
    }


# ---- Usage ----


@router.get("/usage")
async def get_usage_summary(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    repo = WebhookUsageRepo(user_id, session)
    summary = await repo.get_daily_summary(date_from=date_from, date_to=date_to)
    return {
        "success": True,
        "data": [UsageSummary(**s) for s in summary],
    }


@router.get("/{webhook_id}/usage")
async def get_webhook_usage(
    webhook_id: int,
    limit: int = Query(50, ge=1, le=200),
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    # Verify webhook belongs to user
    webhook_repo = WebhookRepo(user_id, session)
    webhook = await webhook_repo.get(webhook_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook key not found")

    usage_repo = WebhookUsageRepo(user_id, session)
    entries = await usage_repo.get_by_webhook(webhook_id, limit=limit)
    return {
        "success": True,
        "data": [UsageEntry(id=e.id, endpoint=e.endpoint, called_at=e.called_at) for e in entries],
    }
