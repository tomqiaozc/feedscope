"""TweAPI.io provider implementing ISocialProvider."""

from __future__ import annotations

import httpx

from app.config import settings
from app.providers.base import (
    AuthRequiredError,
    ProviderTimeoutError,
    RateLimitError,
    UpstreamError,
)
from app.providers.tweapi.normalizer import (
    normalize_analytics,
    normalize_credit_balance,
    normalize_inbox_item,
    normalize_message,
    normalize_tweet,
    normalize_user,
)
from app.providers.tweapi.types import (
    TweAPIAnalyticsResponse,
    TweAPIAuthorList,
    TweAPIConversationResponse,
    TweAPICreditResponse,
    TweAPIInboxList,
    TweAPIListList,
    TweAPISingleAuthor,
    TweAPISingleTweet,
    TweAPITweetList,
)
from app.shared.types import CreditBalance, Post, UserInfo


def _user_url(username: str) -> str:
    return f"https://x.com/{username}"


def _tweet_url(tweet_id: str) -> str:
    return f"https://x.com/i/status/{tweet_id}"


class TweAPIProvider:
    """Twitter data provider using TweAPI.io REST API."""

    def __init__(self, api_key: str, cookie: str | None = None) -> None:
        self._api_key = api_key
        self._cookie = cookie
        timeout = settings.tweapi_timeout_ms / 1000
        self._client = httpx.AsyncClient(
            base_url=settings.tweapi_base_url,
            headers={"x-api-key": api_key, "Content-Type": "application/json"},
            timeout=httpx.Timeout(timeout),
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _require_cookie(self) -> str:
        if not self._cookie:
            raise AuthRequiredError("Twitter cookie is required for this endpoint")
        return self._cookie

    async def _post(self, path: str, body: dict) -> dict:
        try:
            resp = await self._client.post(path, json=body)
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError(str(exc)) from exc

        if resp.status_code == 429:
            retry = resp.headers.get("Retry-After")
            raise RateLimitError(int(retry) if retry else None)
        if resp.status_code >= 400:
            raise UpstreamError(resp.status_code, resp.text[:500])

        data = resp.json()
        if data.get("code") not in (200, 201):
            raise UpstreamError(data.get("code", 0), data.get("msg", "unknown"))
        return data

    async def _get(self, path: str) -> dict:
        try:
            resp = await self._client.get(path)
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError(str(exc)) from exc

        if resp.status_code == 429:
            retry = resp.headers.get("Retry-After")
            raise RateLimitError(int(retry) if retry else None)
        if resp.status_code >= 400:
            raise UpstreamError(resp.status_code, resp.text[:500])

        data = resp.json()
        if data.get("code") not in (200, 201):
            raise UpstreamError(data.get("code", 0), data.get("msg", "unknown"))
        return data

    # ------------------------------------------------------------------
    # ISocialProvider — User info
    # ------------------------------------------------------------------

    async def fetch_user_info(self, username: str) -> UserInfo:
        raw = await self._post("/v1/twitter/user/info", {"url": _user_url(username)})
        parsed = TweAPISingleAuthor.model_validate(raw)
        if parsed.data is None:
            raise UpstreamError(0, "No user data in response")
        return normalize_user(parsed.data)

    # ------------------------------------------------------------------
    # ISocialProvider — User content
    # ------------------------------------------------------------------

    async def fetch_user_tweets(
        self, username: str, *, count: int = 20, cursor: str | None = None
    ) -> list[Post]:
        body: dict = {
            "url": _user_url(username),
            "showPost": True,
            "showReplies": False,
            "showLinks": True,
            "count": count,
        }
        if cursor:
            body["next"] = cursor

        try:
            raw = await self._post("/v1/twitter/user/userRecentTweetsByFilter", body)
        except UpstreamError:
            # Fallback to timeline on any upstream error (400, 500, etc.)
            return await self.fetch_user_timeline(username, count=count, cursor=cursor)

        parsed = TweAPITweetList.model_validate(raw)
        return [normalize_tweet(t) for t in parsed.data.items]

    async def fetch_user_timeline(
        self, username: str, *, count: int = 20, cursor: str | None = None
    ) -> list[Post]:
        body: dict = {"url": _user_url(username)}
        if cursor:
            body["next"] = cursor
        raw = await self._post("/v1/twitter/user/timeline", body)
        parsed = TweAPITweetList.model_validate(raw)
        return [normalize_tweet(t) for t in parsed.data.items]

    async def fetch_user_replies(
        self, username: str, *, count: int = 20, cursor: str | None = None
    ) -> list[Post]:
        body: dict = {"url": _user_url(username)}
        if cursor:
            body["next"] = cursor
        raw = await self._post("/v1/twitter/user/replies", body)
        parsed = TweAPITweetList.model_validate(raw)
        return [normalize_tweet(t) for t in parsed.data.items]

    async def fetch_user_highlights(
        self, username: str, *, count: int = 20, cursor: str | None = None
    ) -> list[Post]:
        body: dict = {"url": _user_url(username)}
        if cursor:
            body["next"] = cursor
        raw = await self._post("/v1/twitter/user/highLights", body)
        parsed = TweAPITweetList.model_validate(raw)
        return [normalize_tweet(t) for t in parsed.data.items]

    # ------------------------------------------------------------------
    # ISocialProvider — Social graph
    # ------------------------------------------------------------------

    async def fetch_followers(
        self, username: str, *, count: int = 20, cursor: str | None = None
    ) -> list[UserInfo]:
        body: dict = {"url": _user_url(username)}
        if cursor:
            body["next"] = cursor
        raw = await self._post("/v1/twitter/user/follower", body)
        parsed = TweAPIAuthorList.model_validate(raw)
        return [normalize_user(a) for a in parsed.data.items]

    async def fetch_following(
        self, username: str, *, count: int = 20, cursor: str | None = None
    ) -> list[UserInfo]:
        body: dict = {"url": _user_url(username)}
        if cursor:
            body["next"] = cursor
        raw = await self._post("/v1/twitter/user/following", body)
        parsed = TweAPIAuthorList.model_validate(raw)
        return [normalize_user(a) for a in parsed.data.items]

    # ------------------------------------------------------------------
    # ISocialProvider — Search
    # ------------------------------------------------------------------

    async def search_tweets(
        self, query: str, *, count: int = 20, cursor: str | None = None
    ) -> list[Post]:
        body: dict = {"words": query, "count": count}
        if cursor:
            body["next"] = cursor
        raw = await self._post("/v1/twitter/tweet/search", body)
        parsed = TweAPITweetList.model_validate(raw)
        return [normalize_tweet(t) for t in parsed.data.items]

    # ------------------------------------------------------------------
    # ISocialProvider — Single tweet
    # ------------------------------------------------------------------

    async def fetch_tweet_details(self, tweet_id: str) -> Post:
        raw = await self._post("/v1/twitter/tweet/details", {"url": _tweet_url(tweet_id)})
        parsed = TweAPISingleTweet.model_validate(raw)
        if parsed.data is None:
            raise UpstreamError(0, "No tweet data in response")
        return normalize_tweet(parsed.data)

    async def fetch_tweet_replies(
        self, tweet_id: str, *, count: int = 20, cursor: str | None = None
    ) -> list[Post]:
        body: dict = {"url": _tweet_url(tweet_id)}
        if cursor:
            body["next"] = cursor
        raw = await self._post("/v1/twitter/tweet/replys", body)
        parsed = TweAPITweetList.model_validate(raw)
        return [normalize_tweet(t) for t in parsed.data.items]

    # ------------------------------------------------------------------
    # ISocialProvider — Authenticated (cookie required)
    # ------------------------------------------------------------------

    async def fetch_bookmarks(self, *, count: int = 20, cursor: str | None = None) -> list[Post]:
        cookie = self._require_cookie()
        body: dict = {"cookie": cookie}
        if cursor:
            body["next"] = cursor
        raw = await self._post("/v1/twitter/user/bookmarks", body)
        parsed = TweAPITweetList.model_validate(raw)
        return [normalize_tweet(t) for t in parsed.data.items]

    async def fetch_likes(
        self, username: str, *, count: int = 20, cursor: str | None = None
    ) -> list[Post]:
        cookie = self._require_cookie()
        body: dict = {"cookie": cookie}
        if cursor:
            body["next"] = cursor
        raw = await self._post("/v1/twitter/user/likes", body)
        parsed = TweAPITweetList.model_validate(raw)
        return [normalize_tweet(t) for t in parsed.data.items]

    # ------------------------------------------------------------------
    # ISocialProvider — Lists
    # ------------------------------------------------------------------

    async def fetch_lists(self, username: str) -> list[dict]:
        cookie = self._require_cookie()
        raw = await self._post("/v1/twitter/user/lists", {"cookie": cookie})
        parsed = TweAPIListList.model_validate(raw)
        return [lst.model_dump() for lst in parsed.data.items]

    async def fetch_list_members(
        self, list_id: str, *, count: int = 20, cursor: str | None = None
    ) -> list[UserInfo]:
        raise NotImplementedError("TweAPI does not support list members endpoint")

    async def fetch_list_tweets(
        self, list_id: str, *, count: int = 20, cursor: str | None = None
    ) -> list[Post]:
        raise NotImplementedError("TweAPI does not support list tweets endpoint")

    # ------------------------------------------------------------------
    # ISocialProvider — DMs / Inbox
    # ------------------------------------------------------------------

    async def fetch_inbox(self, *, cursor: str | None = None) -> list[dict]:
        cookie = self._require_cookie()
        body: dict = {"cookie": cookie}
        if cursor:
            body["next"] = cursor
        raw = await self._post("/v1/twitter/message/inbox", body)
        parsed = TweAPIInboxList.model_validate(raw)
        return [normalize_inbox_item(item) for item in parsed.data.items]

    async def fetch_messages(
        self, conversation_id: str, *, cursor: str | None = None
    ) -> list[dict]:
        cookie = self._require_cookie()
        body: dict = {"cookie": cookie, "conversationId": conversation_id}
        if cursor:
            body["next"] = cursor
        raw = await self._post("/v1/twitter/message/conversation", body)
        parsed = TweAPIConversationResponse.model_validate(raw)
        if parsed.data is None:
            return []
        return [normalize_message(m) for m in parsed.data.messages]

    # ------------------------------------------------------------------
    # ISocialProvider — Analytics
    # ------------------------------------------------------------------

    async def fetch_user_analytics(self, username: str) -> dict:
        cookie = self._require_cookie()
        raw = await self._post("/v1/twitter/user/analytics", {"cookie": cookie})
        parsed = TweAPIAnalyticsResponse.model_validate(raw)
        if parsed.data is None:
            return {}
        return normalize_analytics(parsed.data)

    # ------------------------------------------------------------------
    # ISocialProvider — Credits
    # ------------------------------------------------------------------

    async def fetch_credits(self) -> CreditBalance:
        raw = await self._get("/v1/credits")
        parsed = TweAPICreditResponse.model_validate(raw)
        if parsed.data is None:
            return CreditBalance()
        return normalize_credit_balance(parsed.data)

    # ------------------------------------------------------------------
    # ISocialProvider — Utility
    # ------------------------------------------------------------------

    async def close(self) -> None:
        await self._client.aclose()
