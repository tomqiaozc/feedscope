from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.db.models import UsageDaily
from app.db.repos import BaseRepo


class UsageDailyRepo(BaseRepo):
    async def increment(self, endpoint: str) -> None:
        """Upsert daily count for an endpoint (fire-and-forget)."""
        today = date.today()
        stmt = (
            insert(UsageDaily)
            .values(user_id=self.user_id, endpoint=endpoint, date=today, count=1)
            .on_conflict_do_update(
                index_elements=["user_id", "endpoint", "date"],
                set_={"count": UsageDaily.count + 1},
            )
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def get_summary(
        self,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[UsageDaily]:
        stmt = (
            select(UsageDaily).where(self._user_filter(UsageDaily)).order_by(UsageDaily.date.desc())
        )
        if date_from:
            stmt = stmt.where(UsageDaily.date >= date_from)
        if date_to:
            stmt = stmt.where(UsageDaily.date <= date_to)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())
