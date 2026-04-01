from __future__ import annotations

from sqlalchemy import delete, select

from app.db.models import Tag
from app.db.repos import BaseRepo


class TagRepo(BaseRepo):
    async def list(self, member_id: int) -> list[Tag]:
        result = await self.session.execute(
            select(Tag).where(self._user_filter(Tag), Tag.member_id == member_id)
        )
        return list(result.scalars().all())

    async def create(self, member_id: int, name: str) -> Tag:
        tag = Tag(user_id=self.user_id, member_id=member_id, name=name)
        self.session.add(tag)
        await self.session.flush()
        return tag

    async def delete(self, id: int) -> bool:
        result = await self.session.execute(delete(Tag).where(self._user_filter(Tag), Tag.id == id))
        return result.rowcount > 0

    async def sync(self, member_id: int, tag_names: list[str]) -> list[Tag]:
        """Replace all tags for a member with the given names."""
        await self.session.execute(
            delete(Tag).where(self._user_filter(Tag), Tag.member_id == member_id)
        )
        tags = []
        for name in tag_names:
            tag = Tag(user_id=self.user_id, member_id=member_id, name=name)
            self.session.add(tag)
            tags.append(tag)
        await self.session.flush()
        return tags
