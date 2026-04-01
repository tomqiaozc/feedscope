from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.db.engine import get_db_session
from app.db.repos.profile_repo import ProfileRepo
from app.providers.factory import create_provider_for_user
from app.schemas.groups import ProfileOut, ProfileRefreshRequest

router = APIRouter(prefix="/api/v1/profiles", tags=["profiles"])


@router.post("/refresh")
async def refresh_profiles(
    body: ProfileRefreshRequest,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    if not body.usernames:
        raise HTTPException(status_code=400, detail="At least one username is required")

    provider = await create_provider_for_user(user_id, session)
    if not provider:
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "error": "No Twitter credentials configured. Add a TweAPI key in Settings.",
            },
        )

    profile_repo = ProfileRepo(session)
    sem = asyncio.Semaphore(5)
    results = []
    errors = {}

    async def _fetch_one(username: str):
        async with sem:
            try:
                info = await provider.fetch_user_info(username)
                profile = await profile_repo.upsert(
                    username=info.username,
                    display_name=info.display_name,
                    description=info.description,
                    profile_image_url=info.profile_image_url,
                    followers_count=info.followers_count,
                    following_count=info.following_count,
                    tweet_count=info.tweet_count,
                    is_verified=info.is_verified,
                    location=info.location,
                    website=info.website,
                    joined_at=info.joined_at,
                    profile_json=info.raw_json,
                )
                results.append(profile)
            except Exception as exc:
                errors[username] = str(exc)

    tasks = [asyncio.create_task(_fetch_one(u)) for u in body.usernames]
    await asyncio.gather(*tasks)
    await session.commit()

    return {
        "success": True,
        "data": [
            ProfileOut(
                username=p.username,
                display_name=p.display_name,
                description=p.description,
                profile_image_url=p.profile_image_url,
                followers_count=p.followers_count,
                following_count=p.following_count,
                tweet_count=p.tweet_count,
                is_verified=p.is_verified,
                location=p.location,
                website=p.website,
                joined_at=p.joined_at,
            )
            for p in results
        ],
        "errors": errors if errors else None,
    }
