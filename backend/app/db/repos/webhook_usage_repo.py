from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import func, select

from app.db.models import Webhook, WebhookUsage
from app.db.repos import BaseRepo


class WebhookUsageRepo(BaseRepo):
    async def record(self, webhook_id: int, endpoint: str) -> None:
        """Record a webhook usage event (fire-and-forget)."""
        usage = WebhookUsage(webhook_id=webhook_id, endpoint=endpoint)
        self.session.add(usage)

        # Update last_used_at on the webhook
        result = await self.session.execute(select(Webhook).where(Webhook.id == webhook_id))
        webhook = result.scalar_one_or_none()
        if webhook:
            webhook.last_used_at = datetime.now(UTC)

        await self.session.flush()

    async def get_by_webhook(self, webhook_id: int, limit: int = 50) -> list[WebhookUsage]:
        result = await self.session.execute(
            select(WebhookUsage)
            .where(WebhookUsage.webhook_id == webhook_id)
            .order_by(WebhookUsage.called_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_daily_summary(
        self,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[dict]:
        """Aggregate webhook usage by date and endpoint."""
        stmt = (
            select(
                func.date_trunc("day", WebhookUsage.called_at).label("date"),
                WebhookUsage.endpoint,
                func.count().label("count"),
            )
            .join(Webhook, WebhookUsage.webhook_id == Webhook.id)
            .where(Webhook.user_id == self.user_id)
            .group_by("date", WebhookUsage.endpoint)
            .order_by("date")
        )

        if date_from:
            stmt = stmt.where(
                WebhookUsage.called_at
                >= datetime.combine(date_from, datetime.min.time(), tzinfo=UTC)
            )
        if date_to:
            stmt = stmt.where(
                WebhookUsage.called_at <= datetime.combine(date_to, datetime.max.time(), tzinfo=UTC)
            )

        result = await self.session.execute(stmt)
        return [
            {
                "date": str(row.date.date()) if row.date else None,
                "endpoint": row.endpoint,
                "count": row.count,
            }
            for row in result.all()
        ]
