from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Profile


class ProfileRepo:
    """ProfileRepo is not user-scoped — profiles are shared across users."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_username(self, username: str) -> Profile | None:
        result = await self.session.execute(select(Profile).where(Profile.username == username))
        return result.scalar_one_or_none()

    async def upsert(self, **kwargs) -> Profile:
        stmt = (
            insert(Profile)
            .values(**kwargs)
            .on_conflict_do_update(
                index_elements=["username"],
                set_={k: v for k, v in kwargs.items() if k != "username"},
            )
            .returning(Profile)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def batch_upsert(self, profiles: list[dict]) -> list[Profile]:
        results = []
        for data in profiles:
            profile = await self.upsert(**data)
            results.append(profile)
        await self.session.flush()
        return results
