from __future__ import annotations

from sqlalchemy import delete, func, select

from app.db.models import Group, GroupMember
from app.db.repos import BaseRepo


class GroupRepo(BaseRepo):
    async def list(self) -> list[dict]:
        stmt = (
            select(
                Group,
                func.count(GroupMember.id).label("member_count"),
            )
            .outerjoin(GroupMember, Group.id == GroupMember.group_id)
            .where(self._user_filter(Group))
            .group_by(Group.id)
            .order_by(Group.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return [{"group": row[0], "member_count": row[1]} for row in result.all()]

    async def get(self, id: int) -> Group | None:
        result = await self.session.execute(
            select(Group).where(self._user_filter(Group), Group.id == id)
        )
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> Group:
        group = Group(user_id=self.user_id, **kwargs)
        self.session.add(group)
        await self.session.flush()
        return group

    async def update(self, id: int, **kwargs) -> Group | None:
        group = await self.get(id)
        if not group:
            return None
        for k, v in kwargs.items():
            setattr(group, k, v)
        await self.session.flush()
        await self.session.refresh(group)
        return group

    async def delete(self, id: int) -> bool:
        result = await self.session.execute(
            delete(Group).where(self._user_filter(Group), Group.id == id)
        )
        return result.rowcount > 0
