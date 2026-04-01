from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

from app.db.models import Member
from app.db.repos import BaseRepo


class MemberRepo(BaseRepo):
    async def list(self, watchlist_id: int) -> list[Member]:
        result = await self.session.execute(
            select(Member)
            .options(selectinload(Member.tags))
            .where(
                self._user_filter(Member),
                Member.watchlist_id == watchlist_id,
            )
            .order_by(Member.created_at.desc())
        )
        return list(result.scalars().all())

    async def get(self, id: int) -> Member | None:
        result = await self.session.execute(
            select(Member)
            .options(selectinload(Member.tags))
            .where(self._user_filter(Member), Member.id == id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        watchlist_id: int,
        username: str,
        display_name: str | None = None,
        profile_image_url: str | None = None,
        notes: str | None = None,
    ) -> Member:
        member = Member(
            user_id=self.user_id,
            watchlist_id=watchlist_id,
            username=username,
            display_name=display_name,
            profile_image_url=profile_image_url,
            notes=notes,
        )
        self.session.add(member)
        await self.session.flush()
        return member

    async def update(self, id: int, **kwargs) -> Member | None:
        member = await self.get(id)
        if not member:
            return None
        for key, value in kwargs.items():
            if key == "tags":
                continue  # handled via TagRepo.sync
            if value is not None and hasattr(member, key):
                setattr(member, key, value)
        await self.session.flush()
        return member

    async def delete(self, id: int) -> bool:
        result = await self.session.execute(
            delete(Member).where(self._user_filter(Member), Member.id == id)
        )
        return result.rowcount > 0
