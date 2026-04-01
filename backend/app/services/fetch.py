"""SSE streaming fetch service for watchlist data retrieval."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repos.fetch_log_repo import FetchLogRepo
from app.db.repos.member_repo import MemberRepo
from app.db.repos.post_repo import PostRepo
from app.providers.base import ISocialProvider, ProviderError
from app.services.sse_utils import sse_event


async def fetch_watchlist_stream(
    watchlist_id: int,
    user_id: str,
    session: AsyncSession,
    provider: ISocialProvider,
) -> AsyncGenerator[str, None]:
    member_repo = MemberRepo(user_id, session)
    post_repo = PostRepo(user_id, session)
    fetch_log_repo = FetchLogRepo(user_id, session)

    members = await member_repo.list(watchlist_id)
    total_members = len(members)

    log = await fetch_log_repo.create(
        watchlist_id=watchlist_id,
        type="fetch",
        member_count=total_members,
    )
    await session.commit()

    # Step 1: Cleanup
    yield sse_event("cleanup", {"watchlist_id": watchlist_id})
    await post_repo.delete_by_watchlist(watchlist_id)
    await session.commit()

    total_posts = 0
    error_count = 0
    error_details: dict[str, str] = {}

    try:
        for i, member in enumerate(members):
            # Step 2: Progress
            yield sse_event(
                "progress",
                {
                    "member": member.username,
                    "index": i,
                    "total": total_members,
                },
            )

            try:
                posts = await provider.fetch_user_tweets(member.username)

                post_dicts = []
                for post in posts:
                    post_dicts.append(
                        {
                            "watchlist_id": watchlist_id,
                            "member_id": member.id,
                            "platform_post_id": post.platform_post_id,
                            "author_username": post.author.username,
                            "content": post.content,
                            "post_json": post.raw_json,
                            "metrics": post.metrics.model_dump() if post.metrics else None,
                            "media": [m.model_dump() for m in post.media] if post.media else None,
                            "posted_at": post.posted_at,
                            "fetched_at": datetime.now(UTC),
                        }
                    )

                if post_dicts:
                    await post_repo.bulk_create(post_dicts)
                    await session.commit()

                count = len(post_dicts)
                total_posts += count

                yield sse_event(
                    "posts",
                    {
                        "member": member.username,
                        "count": count,
                    },
                )

            except ProviderError as exc:
                error_count += 1
                error_details[member.username] = str(exc)
                yield sse_event(
                    "error",
                    {
                        "member": member.username,
                        "error": str(exc),
                    },
                )

    except asyncio.CancelledError:
        # Client disconnected
        await fetch_log_repo.update(
            log.id,
            status="cancelled",
            post_count=total_posts,
            error_count=error_count,
            errors=error_details or None,
            completed_at=datetime.now(UTC),
        )
        await session.commit()
        return

    finally:
        await provider.close()

    # Step 3: Done
    await fetch_log_repo.update(
        log.id,
        status="completed",
        post_count=total_posts,
        error_count=error_count,
        errors=error_details or None,
        completed_at=datetime.now(UTC),
    )
    await session.commit()

    yield sse_event(
        "done",
        {
            "total_posts": total_posts,
            "errors": error_count,
        },
    )
