"""Provider factory — returns a configured ISocialProvider instance."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.providers.base import AuthRequiredError, ISocialProvider
from app.providers.mock import MockProvider
from app.providers.tweapi.provider import TweAPIProvider
from app.providers.twitterapi.provider import TwitterAPIProvider


def _make_provider(api_key: str, cookie: str | None = None) -> ISocialProvider:
    if settings.twitter_provider == "twitterapi":
        return TwitterAPIProvider(api_key=api_key, cookie=cookie)  # type: ignore[return-value]
    return TweAPIProvider(api_key=api_key, cookie=cookie)  # type: ignore[return-value]


def create_provider(api_key: str | None = None, cookie: str | None = None) -> ISocialProvider:
    """Create a social provider based on configuration.

    When ``settings.mock_provider`` is True, returns a MockProvider.
    Otherwise returns a provider based on ``settings.twitter_provider``.
    """
    if settings.mock_provider:
        return MockProvider(cookie=cookie)  # type: ignore[return-value]

    if not api_key:
        raise AuthRequiredError("API key is required")

    return _make_provider(api_key, cookie)


async def create_provider_for_user(user_id: str, session: AsyncSession) -> ISocialProvider | None:
    """Load credentials from DB and create a provider.

    Returns None if no credentials are configured.
    """
    if settings.mock_provider:
        return MockProvider()  # type: ignore[return-value]

    from app.db.repos.credentials_repo import CredentialsRepo

    repo = CredentialsRepo(user_id, session)
    cred = await repo.get_by_provider("tweapi")
    if not cred or not cred.api_key:
        return None

    return _make_provider(cred.api_key, cred.cookie)
