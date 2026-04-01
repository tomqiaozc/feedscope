from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.db.engine import get_db_session
from app.db.repos.fetch_log_repo import FetchLogRepo
from app.db.repos.member_repo import MemberRepo
from app.db.repos.post_repo import PostRepo
from app.db.repos.tag_repo import TagRepo
from app.db.repos.watchlist_repo import WatchlistRepo
from app.db.repos.watchlist_settings_repo import WatchlistSettingsRepo
from app.schemas.watchlists import (
    FetchLogOut,
    MemberCreate,
    MemberOut,
    MemberUpdate,
    PostOut,
    WatchlistCreate,
    WatchlistOut,
    WatchlistSettingOut,
    WatchlistSettingUpdate,
    WatchlistUpdate,
)

router = APIRouter(prefix="/api/v1/watchlists", tags=["watchlists"])


def _watchlist_out(wl, member_count: int = 0, post_count: int = 0) -> WatchlistOut:
    return WatchlistOut(
        id=wl.id,
        name=wl.name,
        description=wl.description,
        member_count=member_count,
        post_count=post_count,
        created_at=wl.created_at,
        updated_at=wl.updated_at,
    )


def _member_out(m) -> MemberOut:
    return MemberOut(
        id=m.id,
        username=m.username,
        display_name=m.display_name,
        profile_image_url=m.profile_image_url,
        notes=m.notes,
        tags=[t.name for t in m.tags] if m.tags else [],
        created_at=m.created_at,
    )


def _post_out(p) -> PostOut:
    return PostOut(
        id=p.id,
        platform_post_id=p.platform_post_id,
        author_username=p.author_username,
        content=p.content,
        post_json=p.post_json,
        metrics=p.metrics,
        media=p.media,
        translation=p.translation,
        editorial=p.editorial,
        quoted_translation=p.quoted_translation,
        posted_at=p.posted_at,
        fetched_at=p.fetched_at,
        translated_at=p.translated_at,
    )


def _log_out(log) -> FetchLogOut:
    return FetchLogOut(
        id=log.id,
        type=log.type,
        status=log.status,
        member_count=log.member_count,
        post_count=log.post_count,
        error_count=log.error_count,
        errors=log.errors,
        started_at=log.started_at,
        completed_at=log.completed_at,
    )


# ---- Watchlist CRUD ----


@router.get("")
async def list_watchlists(
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    repo = WatchlistRepo(user_id, session)
    rows = await repo.list_with_counts()
    return {
        "success": True,
        "data": [_watchlist_out(r["watchlist"], r["member_count"], r["post_count"]) for r in rows],
    }


@router.post("", status_code=201)
async def create_watchlist(
    body: WatchlistCreate,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    repo = WatchlistRepo(user_id, session)
    wl = await repo.create(name=body.name, description=body.description)
    return {"success": True, "data": _watchlist_out(wl)}


@router.put("/{watchlist_id}")
async def update_watchlist(
    watchlist_id: int,
    body: WatchlistUpdate,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    repo = WatchlistRepo(user_id, session)
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    wl = await repo.update(watchlist_id, **updates)
    if not wl:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return {"success": True, "data": _watchlist_out(wl)}


@router.delete("/{watchlist_id}")
async def delete_watchlist(
    watchlist_id: int,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    repo = WatchlistRepo(user_id, session)
    deleted = await repo.delete(watchlist_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return {"success": True}


# ---- Members ----


@router.get("/{watchlist_id}/members")
async def list_members(
    watchlist_id: int,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    repo = MemberRepo(user_id, session)
    members = await repo.list(watchlist_id)
    return {"success": True, "data": [_member_out(m) for m in members]}


@router.post("/{watchlist_id}/members", status_code=201)
async def create_member(
    watchlist_id: int,
    body: MemberCreate,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    # Verify watchlist exists
    wl_repo = WatchlistRepo(user_id, session)
    wl = await wl_repo.get(watchlist_id)
    if not wl:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    member_repo = MemberRepo(user_id, session)
    member = await member_repo.create(
        watchlist_id=watchlist_id,
        username=body.username,
        display_name=body.display_name,
        notes=body.notes,
    )

    if body.tags:
        tag_repo = TagRepo(user_id, session)
        await tag_repo.sync(member.id, body.tags)

    # Re-fetch to include tags
    member = await member_repo.get(member.id)
    return {"success": True, "data": _member_out(member)}


@router.put("/{watchlist_id}/members/{member_id}")
async def update_member(
    watchlist_id: int,
    member_id: int,
    body: MemberUpdate,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    member_repo = MemberRepo(user_id, session)
    member = await member_repo.get(member_id)
    if not member or member.watchlist_id != watchlist_id:
        raise HTTPException(status_code=404, detail="Member not found")

    updates = body.model_dump(exclude_none=True, exclude={"tags"})
    if updates:
        await member_repo.update(member_id, **updates)

    if body.tags is not None:
        tag_repo = TagRepo(user_id, session)
        await tag_repo.sync(member_id, body.tags)

    member = await member_repo.get(member_id)
    return {"success": True, "data": _member_out(member)}


@router.delete("/{watchlist_id}/members/{member_id}")
async def delete_member(
    watchlist_id: int,
    member_id: int,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    member_repo = MemberRepo(user_id, session)
    member = await member_repo.get(member_id)
    if not member or member.watchlist_id != watchlist_id:
        raise HTTPException(status_code=404, detail="Member not found")
    await member_repo.delete(member_id)
    return {"success": True}


# ---- Posts ----


@router.get("/{watchlist_id}/posts")
async def list_posts(
    watchlist_id: int,
    tag: str | None = Query(None),
    member_id: int | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    repo = PostRepo(user_id, session)
    posts = await repo.list(watchlist_id, tag=tag, member_id=member_id, offset=offset, limit=limit)
    total = await repo.count(watchlist_id)
    return {"success": True, "data": [_post_out(p) for p in posts], "total": total}


@router.delete("/{watchlist_id}/posts/{post_id}")
async def delete_post(
    watchlist_id: int,
    post_id: int,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    repo = PostRepo(user_id, session)
    post = await repo.get(post_id)
    if not post or post.watchlist_id != watchlist_id:
        raise HTTPException(status_code=404, detail="Post not found")
    await repo.delete(post_id)
    return {"success": True}


# ---- Watchlist Settings ----


@router.get("/{watchlist_id}/settings")
async def get_watchlist_settings(
    watchlist_id: int,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    repo = WatchlistSettingsRepo(user_id, session)
    settings = await repo.get_all(watchlist_id)
    return {
        "success": True,
        "data": [WatchlistSettingOut(key=k, value=v) for k, v in settings.items()],
    }


@router.put("/{watchlist_id}/settings")
async def update_watchlist_settings(
    watchlist_id: int,
    body: WatchlistSettingUpdate,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    repo = WatchlistSettingsRepo(user_id, session)
    await repo.set(watchlist_id, body.key, body.value)
    settings = await repo.get_all(watchlist_id)
    return {
        "success": True,
        "data": [WatchlistSettingOut(key=k, value=v) for k, v in settings.items()],
    }


# ---- Fetch Logs ----


@router.get("/{watchlist_id}/logs")
async def get_fetch_logs(
    watchlist_id: int,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    repo = FetchLogRepo(user_id, session)
    logs = await repo.list(watchlist_id)
    return {"success": True, "data": [_log_out(log) for log in logs]}


# ---- SSE Fetch ----


@router.post("/{watchlist_id}/fetch")
async def fetch_watchlist(
    watchlist_id: int,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    from app.providers.factory import create_provider_for_user
    from app.services.fetch import fetch_watchlist_stream

    # Verify watchlist exists
    wl_repo = WatchlistRepo(user_id, session)
    wl = await wl_repo.get(watchlist_id)
    if not wl:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    provider = await create_provider_for_user(user_id, session)
    if not provider:
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "error": "No Twitter credentials configured. Add a TweAPI key in Settings.",
            },
        )

    return StreamingResponse(
        fetch_watchlist_stream(watchlist_id, user_id, session, provider),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ---- SSE Batch Translate ----


@router.post("/{watchlist_id}/translate")
async def translate_watchlist(
    watchlist_id: int,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    from app.services.batch_translate import batch_translate_stream
    from app.services.translation import load_ai_config

    # Verify watchlist exists
    wl_repo = WatchlistRepo(user_id, session)
    wl = await wl_repo.get(watchlist_id)
    if not wl:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    config = await load_ai_config(user_id, session)
    if not config:
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "error": "No AI provider configured. Add an API key in Settings.",
            },
        )

    return StreamingResponse(
        batch_translate_stream(watchlist_id, user_id, session, config),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
