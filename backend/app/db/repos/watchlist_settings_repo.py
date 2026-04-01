from __future__ import annotations

from sqlalchemy import delete, select

from app.db.models import WatchlistSetting
from app.db.repos import BaseRepo


class WatchlistSettingsRepo(BaseRepo):
    async def get_all(self, watchlist_id: int) -> dict[str, str | None]:
        result = await self.session.execute(
            select(WatchlistSetting).where(
                self._user_filter(WatchlistSetting),
                WatchlistSetting.watchlist_id == watchlist_id,
            )
        )
        return {s.key: s.value for s in result.scalars().all()}

    async def get(self, watchlist_id: int, key: str) -> str | None:
        result = await self.session.execute(
            select(WatchlistSetting).where(
                self._user_filter(WatchlistSetting),
                WatchlistSetting.watchlist_id == watchlist_id,
                WatchlistSetting.key == key,
            )
        )
        setting = result.scalar_one_or_none()
        return setting.value if setting else None

    async def set(self, watchlist_id: int, key: str, value: str) -> WatchlistSetting:
        result = await self.session.execute(
            select(WatchlistSetting).where(
                self._user_filter(WatchlistSetting),
                WatchlistSetting.watchlist_id == watchlist_id,
                WatchlistSetting.key == key,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.value = value
            await self.session.flush()
            return existing
        setting = WatchlistSetting(
            user_id=self.user_id,
            watchlist_id=watchlist_id,
            key=key,
            value=value,
        )
        self.session.add(setting)
        await self.session.flush()
        return setting

    async def delete(self, watchlist_id: int, key: str) -> bool:
        result = await self.session.execute(
            delete(WatchlistSetting).where(
                self._user_filter(WatchlistSetting),
                WatchlistSetting.watchlist_id == watchlist_id,
                WatchlistSetting.key == key,
            )
        )
        return result.rowcount > 0
