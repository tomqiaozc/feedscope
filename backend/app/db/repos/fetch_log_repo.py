from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select

from app.db.models import FetchLog
from app.db.repos import BaseRepo


class FetchLogRepo(BaseRepo):
    async def list(self, watchlist_id: int) -> list[FetchLog]:
        result = await self.session.execute(
            select(FetchLog)
            .where(
                self._user_filter(FetchLog),
                FetchLog.watchlist_id == watchlist_id,
            )
            .order_by(FetchLog.started_at.desc().nullslast())
        )
        return list(result.scalars().all())

    async def create(
        self,
        watchlist_id: int,
        type: str,
        status: str = "running",
        member_count: int | None = None,
    ) -> FetchLog:
        log = FetchLog(
            user_id=self.user_id,
            watchlist_id=watchlist_id,
            type=type,
            status=status,
            member_count=member_count,
            started_at=datetime.now(UTC),
        )
        self.session.add(log)
        await self.session.flush()
        return log

    async def update(
        self,
        id: int,
        *,
        status: str | None = None,
        post_count: int | None = None,
        error_count: int | None = None,
        errors: dict | None = None,
        completed_at: datetime | None = None,
    ) -> FetchLog | None:
        result = await self.session.execute(
            select(FetchLog).where(self._user_filter(FetchLog), FetchLog.id == id)
        )
        log = result.scalar_one_or_none()
        if not log:
            return None
        if status is not None:
            log.status = status
        if post_count is not None:
            log.post_count = post_count
        if error_count is not None:
            log.error_count = error_count
        if errors is not None:
            log.errors = errors
        if completed_at is not None:
            log.completed_at = completed_at
        await self.session.flush()
        return log
