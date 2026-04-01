from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.db.engine import get_db_session
from app.providers.factory import create_provider_for_user
from app.schemas.explore import PostOut, UserInfoOut

router = APIRouter(prefix="/api/v1/explore", tags=["explore"])


def _post_out(p) -> PostOut:
    return PostOut(
        platform_post_id=p.platform_post_id,
        author_username=p.author.username,
        author_display_name=p.author.display_name,
        author_profile_image_url=p.author.profile_image_url,
        author_is_verified=p.author.is_verified,
        content=p.content,
        posted_at=p.posted_at,
        metrics=p.metrics.model_dump() if p.metrics else None,
        media=[m.model_dump() for m in p.media] if p.media else None,
        quoted_post=_post_out(p.quoted_post) if p.quoted_post else None,
        is_retweet=p.is_retweet,
        is_reply=p.is_reply,
        language=p.language,
    )


def _user_out(u) -> UserInfoOut:
    return UserInfoOut(
        username=u.username,
        display_name=u.display_name,
        description=u.description,
        profile_image_url=u.profile_image_url,
        followers_count=u.followers_count,
        following_count=u.following_count,
        tweet_count=u.tweet_count,
        is_verified=u.is_verified,
        location=u.location,
        website=u.website,
        joined_at=u.joined_at,
    )


async def _get_provider(user_id: str, session: AsyncSession):
    provider = await create_provider_for_user(user_id, session)
    if not provider:
        return None
    return provider


def _no_creds_response():
    return JSONResponse(
        status_code=503,
        content={
            "success": False,
            "error": "No Twitter credentials configured. Add a TweAPI key in Settings.",
        },
    )


# ---- Search ----


@router.get("/search")
async def search_tweets(
    q: str = Query(..., min_length=1),
    count: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    provider = await _get_provider(user_id, session)
    if not provider:
        return _no_creds_response()
    posts = await provider.search_tweets(q, count=count)
    return {"success": True, "data": [_post_out(p) for p in posts]}


# ---- User profile ----


@router.get("/user/{username}")
async def get_user_info(
    username: str,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    provider = await _get_provider(user_id, session)
    if not provider:
        return _no_creds_response()
    info = await provider.fetch_user_info(username)
    return {"success": True, "data": _user_out(info)}


# ---- User content ----


@router.get("/user/{username}/tweets")
async def get_user_tweets(
    username: str,
    count: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    provider = await _get_provider(user_id, session)
    if not provider:
        return _no_creds_response()
    posts = await provider.fetch_user_tweets(username, count=count)
    return {"success": True, "data": [_post_out(p) for p in posts]}


@router.get("/user/{username}/timeline")
async def get_user_timeline(
    username: str,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    provider = await _get_provider(user_id, session)
    if not provider:
        return _no_creds_response()
    posts = await provider.fetch_user_timeline(username)
    return {"success": True, "data": [_post_out(p) for p in posts]}


@router.get("/user/{username}/replies")
async def get_user_replies(
    username: str,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    provider = await _get_provider(user_id, session)
    if not provider:
        return _no_creds_response()
    posts = await provider.fetch_user_replies(username)
    return {"success": True, "data": [_post_out(p) for p in posts]}


@router.get("/user/{username}/highlights")
async def get_user_highlights(
    username: str,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    provider = await _get_provider(user_id, session)
    if not provider:
        return _no_creds_response()
    posts = await provider.fetch_user_highlights(username)
    return {"success": True, "data": [_post_out(p) for p in posts]}


# ---- Social graph ----


@router.get("/user/{username}/followers")
async def get_user_followers(
    username: str,
    count: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    provider = await _get_provider(user_id, session)
    if not provider:
        return _no_creds_response()
    users = await provider.fetch_followers(username, count=count)
    return {"success": True, "data": [_user_out(u) for u in users]}


@router.get("/user/{username}/following")
async def get_user_following(
    username: str,
    count: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    provider = await _get_provider(user_id, session)
    if not provider:
        return _no_creds_response()
    users = await provider.fetch_following(username, count=count)
    return {"success": True, "data": [_user_out(u) for u in users]}


# ---- Bookmarks / Likes (cookie auth required) ----


@router.get("/bookmarks")
async def get_bookmarks(
    count: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    provider = await _get_provider(user_id, session)
    if not provider:
        return _no_creds_response()
    posts = await provider.fetch_bookmarks(count=count)
    return {"success": True, "data": [_post_out(p) for p in posts]}


@router.get("/likes")
async def get_likes(
    username: str = Query(...),
    count: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    provider = await _get_provider(user_id, session)
    if not provider:
        return _no_creds_response()
    posts = await provider.fetch_likes(username, count=count)
    return {"success": True, "data": [_post_out(p) for p in posts]}


# ---- Single tweet ----


@router.get("/tweet/{tweet_id}")
async def get_tweet_details(
    tweet_id: str,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    provider = await _get_provider(user_id, session)
    if not provider:
        return _no_creds_response()
    post = await provider.fetch_tweet_details(tweet_id)
    return {"success": True, "data": _post_out(post)}


@router.get("/tweet/{tweet_id}/replies")
async def get_tweet_replies(
    tweet_id: str,
    count: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    provider = await _get_provider(user_id, session)
    if not provider:
        return _no_creds_response()
    posts = await provider.fetch_tweet_replies(tweet_id, count=count)
    return {"success": True, "data": [_post_out(p) for p in posts]}
