from __future__ import annotations

from sqlalchemy import delete, func, select

from app.db.models import Member, Post, Tag
from app.db.repos import BaseRepo


class PostRepo(BaseRepo):
    async def list(
        self,
        watchlist_id: int,
        *,
        tag: str | None = None,
        member_id: int | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Post]:
        stmt = select(Post).where(
            self._user_filter(Post),
            Post.watchlist_id == watchlist_id,
        )

        if member_id is not None:
            stmt = stmt.where(Post.member_id == member_id)

        if tag is not None:
            stmt = (
                stmt.join(Member, Post.member_id == Member.id)
                .join(Tag, Tag.member_id == Member.id)
                .where(Tag.name == tag)
            )

        stmt = stmt.order_by(Post.posted_at.desc().nullslast()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get(self, id: int) -> Post | None:
        result = await self.session.execute(
            select(Post).where(self._user_filter(Post), Post.id == id)
        )
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> Post:
        post = Post(user_id=self.user_id, **kwargs)
        self.session.add(post)
        await self.session.flush()
        return post

    async def bulk_create(self, posts: list[dict]) -> list[Post]:
        objs = []
        for data in posts:
            post = Post(user_id=self.user_id, **data)
            self.session.add(post)
            objs.append(post)
        await self.session.flush()
        return objs

    async def delete(self, id: int) -> bool:
        result = await self.session.execute(
            delete(Post).where(self._user_filter(Post), Post.id == id)
        )
        return result.rowcount > 0

    async def delete_by_watchlist(self, watchlist_id: int) -> int:
        result = await self.session.execute(
            delete(Post).where(self._user_filter(Post), Post.watchlist_id == watchlist_id)
        )
        return result.rowcount

    async def update(self, id: int, **kwargs) -> Post | None:
        result = await self.session.execute(
            select(Post).where(self._user_filter(Post), Post.id == id)
        )
        post = result.scalar_one_or_none()
        if not post:
            return None
        for k, v in kwargs.items():
            setattr(post, k, v)
        await self.session.flush()
        return post

    async def list_untranslated(self, watchlist_id: int) -> list[Post]:
        result = await self.session.execute(
            select(Post)
            .where(
                self._user_filter(Post),
                Post.watchlist_id == watchlist_id,
                Post.translated_at.is_(None),
            )
            .order_by(Post.posted_at.desc().nullslast())
        )
        return list(result.scalars().all())

    async def count(self, watchlist_id: int) -> int:
        result = await self.session.scalar(
            select(func.count(Post.id)).where(
                self._user_filter(Post), Post.watchlist_id == watchlist_id
            )
        )
        return result or 0
