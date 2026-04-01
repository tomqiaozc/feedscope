from sqlalchemy import delete, select

from app.db.models import Setting
from app.db.repos import BaseRepo


class SettingsRepo(BaseRepo):
    async def get(self, key: str) -> str | None:
        result = await self.session.execute(
            select(Setting.value).where(self._user_filter(Setting), Setting.key == key)
        )
        return result.scalar_one_or_none()

    async def get_many(self, prefix: str) -> dict[str, str | None]:
        result = await self.session.execute(
            select(Setting).where(self._user_filter(Setting), Setting.key.startswith(prefix))
        )
        return {s.key: s.value for s in result.scalars().all()}

    async def set(self, key: str, value: str | None) -> Setting:
        result = await self.session.execute(
            select(Setting).where(self._user_filter(Setting), Setting.key == key)
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.value = value
            await self.session.flush()
            return existing
        setting = Setting(user_id=self.user_id, key=key, value=value)
        self.session.add(setting)
        await self.session.flush()
        return setting

    async def delete(self, key: str) -> bool:
        result = await self.session.execute(
            delete(Setting).where(self._user_filter(Setting), Setting.key == key)
        )
        return result.rowcount > 0
