"""SSE streaming batch translation service for watchlist posts."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import async_session_factory
from app.db.repos.fetch_log_repo import FetchLogRepo
from app.db.repos.post_repo import PostRepo
from app.services.sse_utils import sse_event
from app.services.translation import AiConfig, translate_post


async def batch_translate_stream(
    watchlist_id: int,
    user_id: str,
    session: AsyncSession,
    config: AiConfig,
) -> AsyncGenerator[str, None]:
    post_repo = PostRepo(user_id, session)
    fetch_log_repo = FetchLogRepo(user_id, session)

    posts = await post_repo.list_untranslated(watchlist_id)
    total = len(posts)

    log = await fetch_log_repo.create(
        watchlist_id=watchlist_id,
        type="translate",
        post_count=0,
    )
    await session.commit()

    yield sse_event("start", {"watchlist_id": watchlist_id, "total": total})

    if total == 0:
        await fetch_log_repo.update(
            log.id,
            status="completed",
            post_count=0,
            error_count=0,
            completed_at=datetime.now(UTC),
        )
        await session.commit()
        yield sse_event("done", {"translated": 0, "errors": 0})
        return

    translated_count = 0
    error_count = 0
    error_details: dict[str, str] = {}
    sem = asyncio.Semaphore(3)

    async def _translate_one(post, index: int) -> tuple[str, dict]:
        """Translate a single post using an independent DB session."""
        async with sem:
            try:
                quoted_content = None
                if post.post_json and isinstance(post.post_json, dict):
                    qt = post.post_json.get("quotedTweet") or post.post_json.get("quoted_tweet")
                    if qt and isinstance(qt, dict):
                        quoted_content = qt.get("content") or qt.get("text")

                result = await translate_post(
                    post.content or "",
                    config,
                    quoted_content=quoted_content,
                )

                # Use independent session for DB write to avoid concurrent access
                async with async_session_factory() as db:
                    task_repo = PostRepo(user_id, db)
                    await task_repo.update(
                        post.id,
                        translation=result.translation,
                        editorial=result.editorial,
                        quoted_translation=result.quoted_translation,
                        translated_at=datetime.now(UTC),
                    )
                    await db.commit()

                return "translated", {
                    "post_id": post.id,
                    "index": index,
                    "total": total,
                    "translation": result.translation,
                }
            except Exception as exc:
                return "error", {
                    "post_id": post.id,
                    "index": index,
                    "error": str(exc),
                }

    try:
        tasks: list[asyncio.Task] = []
        for i, post in enumerate(posts):
            yield sse_event(
                "translating",
                {
                    "post_id": post.id,
                    "index": i,
                    "total": total,
                },
            )
            tasks.append(asyncio.create_task(_translate_one(post, i)))

        for task in tasks:
            event_type, event_data = await task
            if event_type == "translated":
                translated_count += 1
            else:
                error_count += 1
                error_details[str(event_data.get("post_id", ""))] = event_data.get("error", "")
            yield sse_event(event_type, event_data)

    except asyncio.CancelledError:
        for task in tasks:
            if not task.done():
                task.cancel()
        await fetch_log_repo.update(
            log.id,
            status="cancelled",
            post_count=translated_count,
            error_count=error_count,
            errors=error_details or None,
            completed_at=datetime.now(UTC),
        )
        await session.commit()
        return

    await fetch_log_repo.update(
        log.id,
        status="completed",
        post_count=translated_count,
        error_count=error_count,
        errors=error_details or None,
        completed_at=datetime.now(UTC),
    )
    await session.commit()

    yield sse_event(
        "done",
        {
            "translated": translated_count,
            "errors": error_count,
        },
    )
