from __future__ import annotations

from sqlalchemy import delete, func, select

from app.db.models import Member, Post, Watchlist
from app.db.repos import BaseRepo


class WatchlistRepo(BaseRepo):
    async def list(self) -> list[Watchlist]:
        result = await self.session.execute(
            select(Watchlist)
            .where(self._user_filter(Watchlist))
            .order_by(Watchlist.created_at.desc())
        )
        return list(result.scalars().all())

    async def get(self, id: int) -> Watchlist | None:
        result = await self.session.execute(
            select(Watchlist).where(self._user_filter(Watchlist), Watchlist.id == id)
        )
        return result.scalar_one_or_none()

    async def create(self, name: str, description: str | None = None) -> Watchlist:
        wl = Watchlist(user_id=self.user_id, name=name, description=description)
        self.session.add(wl)
        await self.session.flush()
        return wl

    async def update(self, id: int, **kwargs) -> Watchlist | None:
        wl = await self.get(id)
        if not wl:
            return None
        for key, value in kwargs.items():
            if value is not None and hasattr(wl, key):
                setattr(wl, key, value)
        await self.session.flush()
        await self.session.refresh(wl)
        return wl

    async def delete(self, id: int) -> bool:
        result = await self.session.execute(
            delete(Watchlist).where(self._user_filter(Watchlist), Watchlist.id == id)
        )
        return result.rowcount > 0

    async def list_with_counts(self) -> list[dict]:
        member_sub = (
            select(Member.watchlist_id, func.count(Member.id).label("member_count"))
            .where(self._user_filter(Member))
            .group_by(Member.watchlist_id)
            .subquery()
        )
        post_sub = (
            select(Post.watchlist_id, func.count(Post.id).label("post_count"))
            .where(self._user_filter(Post))
            .group_by(Post.watchlist_id)
            .subquery()
        )
        stmt = (
            select(
                Watchlist,
                func.coalesce(member_sub.c.member_count, 0).label("member_count"),
                func.coalesce(post_sub.c.post_count, 0).label("post_count"),
            )
            .outerjoin(member_sub, Watchlist.id == member_sub.c.watchlist_id)
            .outerjoin(post_sub, Watchlist.id == post_sub.c.watchlist_id)
            .where(self._user_filter(Watchlist))
            .order_by(Watchlist.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return [
            {"watchlist": row[0], "member_count": row[1], "post_count": row[2]}
            for row in result.all()
        ]
