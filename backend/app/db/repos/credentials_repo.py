from sqlalchemy import delete, select

from app.db.models import Credential
from app.db.repos import BaseRepo


class CredentialsRepo(BaseRepo):
    async def list(self) -> list[Credential]:
        result = await self.session.execute(select(Credential).where(self._user_filter(Credential)))
        return list(result.scalars().all())

    async def get_by_provider(self, provider: str) -> Credential | None:
        result = await self.session.execute(
            select(Credential).where(self._user_filter(Credential), Credential.provider == provider)
        )
        return result.scalar_one_or_none()

    async def upsert(
        self, provider: str, api_key: str | None = None, cookie: str | None = None
    ) -> Credential:
        existing = await self.get_by_provider(provider)
        if existing:
            if api_key is not None:
                existing.api_key = api_key
            if cookie is not None:
                existing.cookie = cookie
            await self.session.flush()
            return existing
        cred = Credential(user_id=self.user_id, provider=provider, api_key=api_key, cookie=cookie)
        self.session.add(cred)
        await self.session.flush()
        return cred

    async def delete(self, provider: str) -> bool:
        result = await self.session.execute(
            delete(Credential).where(self._user_filter(Credential), Credential.provider == provider)
        )
        return result.rowcount > 0
