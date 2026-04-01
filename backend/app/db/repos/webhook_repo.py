from __future__ import annotations

from sqlalchemy import delete, select

from app.db.models import Webhook
from app.db.repos import BaseRepo
from app.utils.crypto import generate_webhook_key, hash_key, key_prefix, verify_key


class WebhookRepo(BaseRepo):
    async def list(self) -> list[Webhook]:
        result = await self.session.execute(
            select(Webhook).where(self._user_filter(Webhook)).order_by(Webhook.created_at.desc())
        )
        return list(result.scalars().all())

    async def get(self, id: int) -> Webhook | None:
        result = await self.session.execute(
            select(Webhook).where(self._user_filter(Webhook), Webhook.id == id)
        )
        return result.scalar_one_or_none()

    async def create(self, name: str) -> tuple[Webhook, str]:
        """Create a new webhook key. Returns (webhook, full_key).
        The full key is only available at creation time.
        """
        raw_key = generate_webhook_key()
        webhook = Webhook(
            user_id=self.user_id,
            name=name,
            key_prefix=key_prefix(raw_key),
            key_hash=hash_key(raw_key),
        )
        self.session.add(webhook)
        await self.session.flush()
        return webhook, raw_key

    async def delete(self, id: int) -> bool:
        result = await self.session.execute(
            delete(Webhook).where(self._user_filter(Webhook), Webhook.id == id)
        )
        return result.rowcount > 0

    async def rotate(self, id: int) -> tuple[Webhook, str] | None:
        """Rotate a webhook key. Returns (webhook, new_key) or None if not found."""
        webhook = await self.get(id)
        if not webhook:
            return None
        raw_key = generate_webhook_key()
        webhook.key_prefix = key_prefix(raw_key)
        webhook.key_hash = hash_key(raw_key)
        await self.session.flush()
        return webhook, raw_key

    async def verify(self, key_string: str) -> tuple[str, int] | None:
        """Verify a webhook key. Returns (user_id, webhook_id) or None.
        Scans all keys — acceptable for small key counts.
        """
        result = await self.session.execute(select(Webhook.id, Webhook.user_id, Webhook.key_hash))
        for row in result.all():
            if verify_key(key_string, row.key_hash):
                return row.user_id, row.id
        return None
