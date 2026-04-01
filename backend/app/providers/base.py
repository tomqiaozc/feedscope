from typing import Protocol

from app.shared.types import CreditBalance, Post, UserInfo


class ProviderError(Exception):
    """Base error for all provider errors."""


class UpstreamError(ProviderError):
    """The upstream API returned an error."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"Upstream error {status_code}: {message}")


class AuthRequiredError(ProviderError):
    """Authentication credentials are missing or invalid."""


class RateLimitError(ProviderError):
    """Rate limit exceeded."""

    def __init__(self, retry_after: int | None = None):
        self.retry_after = retry_after
        super().__init__(f"Rate limited{f', retry after {retry_after}s' if retry_after else ''}")


class ProviderTimeoutError(ProviderError):
    """Request timed out."""


class ISocialProvider(Protocol):
    # --- User info ---
    async def fetch_user_info(self, username: str) -> UserInfo: ...

    # --- User content ---
    async def fetch_user_tweets(
        self, username: str, *, count: int = 20, cursor: str | None = None
    ) -> list[Post]: ...

    async def fetch_user_timeline(
        self, username: str, *, count: int = 20, cursor: str | None = None
    ) -> list[Post]: ...

    async def fetch_user_replies(
        self, username: str, *, count: int = 20, cursor: str | None = None
    ) -> list[Post]: ...

    async def fetch_user_highlights(
        self, username: str, *, count: int = 20, cursor: str | None = None
    ) -> list[Post]: ...

    # --- Social graph ---
    async def fetch_followers(
        self, username: str, *, count: int = 20, cursor: str | None = None
    ) -> list[UserInfo]: ...

    async def fetch_following(
        self, username: str, *, count: int = 20, cursor: str | None = None
    ) -> list[UserInfo]: ...

    # --- Search ---
    async def search_tweets(
        self, query: str, *, count: int = 20, cursor: str | None = None
    ) -> list[Post]: ...

    # --- Single tweet ---
    async def fetch_tweet_details(self, tweet_id: str) -> Post: ...

    async def fetch_tweet_replies(
        self, tweet_id: str, *, count: int = 20, cursor: str | None = None
    ) -> list[Post]: ...

    # --- Authenticated user content (requires cookie) ---
    async def fetch_bookmarks(
        self, *, count: int = 20, cursor: str | None = None
    ) -> list[Post]: ...

    async def fetch_likes(
        self, username: str, *, count: int = 20, cursor: str | None = None
    ) -> list[Post]: ...

    # --- Lists ---
    async def fetch_lists(self, username: str) -> list[dict]: ...

    async def fetch_list_members(
        self, list_id: str, *, count: int = 20, cursor: str | None = None
    ) -> list[UserInfo]: ...

    async def fetch_list_tweets(
        self, list_id: str, *, count: int = 20, cursor: str | None = None
    ) -> list[Post]: ...

    # --- DMs / Inbox ---
    async def fetch_inbox(self, *, cursor: str | None = None) -> list[dict]: ...

    async def fetch_messages(
        self, conversation_id: str, *, cursor: str | None = None
    ) -> list[dict]: ...

    # --- Analytics ---
    async def fetch_user_analytics(self, username: str) -> dict: ...

    # --- Credits / usage ---
    async def fetch_credits(self) -> CreditBalance: ...

    # --- Utility ---
    async def close(self) -> None: ...
