from __future__ import annotations

from sqlalchemy import delete, select

from app.db.models import GroupMember
from app.db.repos import BaseRepo


class GroupMemberRepo(BaseRepo):
    async def list(self, group_id: int) -> list[GroupMember]:
        result = await self.session.execute(
            select(GroupMember)
            .where(self._user_filter(GroupMember), GroupMember.group_id == group_id)
            .order_by(GroupMember.created_at.desc())
        )
        return list(result.scalars().all())

    async def get(self, id: int) -> GroupMember | None:
        result = await self.session.execute(
            select(GroupMember).where(self._user_filter(GroupMember), GroupMember.id == id)
        )
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> GroupMember:
        member = GroupMember(user_id=self.user_id, **kwargs)
        self.session.add(member)
        await self.session.flush()
        return member

    async def batch_create(self, group_id: int, members: list[dict]) -> list[GroupMember]:
        objs = []
        for data in members:
            member = GroupMember(user_id=self.user_id, group_id=group_id, **data)
            self.session.add(member)
            objs.append(member)
        await self.session.flush()
        return objs

    async def delete(self, id: int) -> bool:
        result = await self.session.execute(
            delete(GroupMember).where(self._user_filter(GroupMember), GroupMember.id == id)
        )
        return result.rowcount > 0

    async def batch_delete(self, group_id: int, member_ids: list[int]) -> int:
        result = await self.session.execute(
            delete(GroupMember).where(
                self._user_filter(GroupMember),
                GroupMember.group_id == group_id,
                GroupMember.id.in_(member_ids),
            )
        )
        return result.rowcount
