"""TwitterAPI.io provider implementing ISocialProvider."""

from __future__ import annotations

import httpx

from app.config import settings
from app.providers.base import (
    AuthRequiredError,
    ProviderTimeoutError,
    RateLimitError,
    UpstreamError,
)
from app.providers.twitterapi.normalizer import (
    normalize_follower_user,
    normalize_tweet,
    normalize_user,
)
from app.providers.twitterapi.types import (
    TAFollowersResponse,
    TAFollowingResponse,
    TASearchResponse,
    TATweetsById,
    TAUserInfoResponse,
    TAUserTweetsResponse,
)
from app.shared.types import CreditBalance, Post, UserInfo


class TwitterAPIProvider:
    """Twitter data provider using TwitterAPI.io REST API."""

    def __init__(self, api_key: str, cookie: str | None = None) -> None:
        self._api_key = api_key
        self._cookie = cookie
        timeout = settings.twitterapi_timeout_ms / 1000
        self._client = httpx.AsyncClient(
            base_url=settings.twitterapi_base_url,
            headers={"X-API-Key": api_key},
            timeout=httpx.Timeout(timeout),
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _get(self, path: str, params: dict | None = None) -> dict:
        try:
            resp = await self._client.get(path, params=params)
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError(str(exc)) from exc

        if resp.status_code == 429:
            retry = resp.headers.get("Retry-After")
            raise RateLimitError(int(retry) if retry else None)
        if resp.status_code == 401:
            raise AuthRequiredError("Invalid TwitterAPI.io API key")
        if resp.status_code >= 400:
            raise UpstreamError(resp.status_code, resp.text[:500])

        return resp.json()

    # ------------------------------------------------------------------
    # ISocialProvider — User info
    # ------------------------------------------------------------------

    async def fetch_user_info(self, username: str) -> UserInfo:
        raw = await self._get("/twitter/user/info", {"userName": username})
        parsed = TAUserInfoResponse.model_validate(raw)
        if parsed.data is None:
            raise UpstreamError(0, "No user data in response")
        return normalize_user(parsed.data)

    # ------------------------------------------------------------------
    # ISocialProvider — User content
    # ------------------------------------------------------------------

    async def fetch_user_tweets(
        self, username: str, *, count: int = 20, cursor: str | None = None
    ) -> list[Post]:
        params: dict = {"userName": username, "count": count}
        if cursor:
            params["cursor"] = cursor
        raw = await self._get("/twitter/user/last_tweets", params)
        parsed = TAUserTweetsResponse.model_validate(raw)
        if not parsed.data or not parsed.data.tweets:
            return []
        return [normalize_tweet(t) for t in parsed.data.tweets]

    async def fetch_user_timeline(
        self, username: str, *, count: int = 20, cursor: str | None = None
    ) -> list[Post]:
        # TwitterAPI.io uses same endpoint for tweets and timeline
        return await self.fetch_user_tweets(username, count=count, cursor=cursor)

    async def fetch_user_replies(
        self, username: str, *, count: int = 20, cursor: str | None = None
    ) -> list[Post]:
        # Use search with from:username filter to get replies
        params: dict = {
            "query": f"from:{username}",
            "queryType": "Latest",
            "count": count,
        }
        if cursor:
            params["cursor"] = cursor
        raw = await self._get("/twitter/tweet/advanced_search", params)
        parsed = TASearchResponse.model_validate(raw)
        tweets = [normalize_tweet(t) for t in parsed.tweets]
        return [t for t in tweets if t.is_reply]

    async def fetch_user_highlights(
        self, username: str, *, count: int = 20, cursor: str | None = None
    ) -> list[Post]:
        # TwitterAPI.io doesn't have a dedicated highlights endpoint;
        # fall back to regular tweets
        return await self.fetch_user_tweets(username, count=count, cursor=cursor)

    # ------------------------------------------------------------------
    # ISocialProvider — Social graph
    # ------------------------------------------------------------------

    async def fetch_followers(
        self, username: str, *, count: int = 20, cursor: str | None = None
    ) -> list[UserInfo]:
        params: dict = {"userName": username, "count": count}
        if cursor:
            params["cursor"] = cursor
        raw = await self._get("/twitter/user/followers", params)
        parsed = TAFollowersResponse.model_validate(raw)
        return [normalize_follower_user(f) for f in parsed.followers]

    async def fetch_following(
        self, username: str, *, count: int = 20, cursor: str | None = None
    ) -> list[UserInfo]:
        params: dict = {"userName": username, "count": count}
        if cursor:
            params["cursor"] = cursor
        raw = await self._get("/twitter/user/following", params)
        parsed = TAFollowingResponse.model_validate(raw)
        return [normalize_follower_user(f) for f in parsed.following]

    # ------------------------------------------------------------------
    # ISocialProvider — Search
    # ------------------------------------------------------------------

    async def search_tweets(
        self, query: str, *, count: int = 20, cursor: str | None = None
    ) -> list[Post]:
        params: dict = {"query": query, "queryType": "Latest", "count": count}
        if cursor:
            params["cursor"] = cursor
        raw = await self._get("/twitter/tweet/advanced_search", params)
        parsed = TASearchResponse.model_validate(raw)
        return [normalize_tweet(t) for t in parsed.tweets]

    # ------------------------------------------------------------------
    # ISocialProvider — Single tweet
    # ------------------------------------------------------------------

    async def fetch_tweet_details(self, tweet_id: str) -> Post:
        raw = await self._get("/twitter/tweets", {"tweet_ids": tweet_id})
        parsed = TATweetsById.model_validate(raw)
        if not parsed.tweets:
            raise UpstreamError(0, "No tweet data in response")
        return normalize_tweet(parsed.tweets[0])

    async def fetch_tweet_replies(
        self, tweet_id: str, *, count: int = 20, cursor: str | None = None
    ) -> list[Post]:
        # Use search to find replies to a specific tweet
        params: dict = {
            "query": f"conversation_id:{tweet_id}",
            "queryType": "Latest",
            "count": count,
        }
        if cursor:
            params["cursor"] = cursor
        raw = await self._get("/twitter/tweet/advanced_search", params)
        parsed = TASearchResponse.model_validate(raw)
        return [normalize_tweet(t) for t in parsed.tweets]

    # ------------------------------------------------------------------
    # ISocialProvider — Authenticated (not supported)
    # ------------------------------------------------------------------

    async def fetch_bookmarks(self, *, count: int = 20, cursor: str | None = None) -> list[Post]:
        raise NotImplementedError("TwitterAPI.io does not support bookmarks endpoint")

    async def fetch_likes(
        self, username: str, *, count: int = 20, cursor: str | None = None
    ) -> list[Post]:
        raise NotImplementedError("TwitterAPI.io does not support likes endpoint")

    # ------------------------------------------------------------------
    # ISocialProvider — Lists (not supported)
    # ------------------------------------------------------------------

    async def fetch_lists(self, username: str) -> list[dict]:
        raise NotImplementedError("TwitterAPI.io does not support lists endpoint")

    async def fetch_list_members(
        self, list_id: str, *, count: int = 20, cursor: str | None = None
    ) -> list[UserInfo]:
        raise NotImplementedError("TwitterAPI.io does not support list members endpoint")

    async def fetch_list_tweets(
        self, list_id: str, *, count: int = 20, cursor: str | None = None
    ) -> list[Post]:
        raise NotImplementedError("TwitterAPI.io does not support list tweets endpoint")

    # ------------------------------------------------------------------
    # ISocialProvider — DMs / Inbox (not supported)
    # ------------------------------------------------------------------

    async def fetch_inbox(self, *, cursor: str | None = None) -> list[dict]:
        raise NotImplementedError("TwitterAPI.io does not support inbox endpoint")

    async def fetch_messages(
        self, conversation_id: str, *, cursor: str | None = None
    ) -> list[dict]:
        raise NotImplementedError("TwitterAPI.io does not support messages endpoint")

    # ------------------------------------------------------------------
    # ISocialProvider — Analytics (not supported)
    # ------------------------------------------------------------------

    async def fetch_user_analytics(self, username: str) -> dict:
        raise NotImplementedError("TwitterAPI.io does not support analytics endpoint")

    # ------------------------------------------------------------------
    # ISocialProvider — Credits
    # ------------------------------------------------------------------

    async def fetch_credits(self) -> CreditBalance:
        # TwitterAPI.io doesn't have a credits endpoint in the same way
        return CreditBalance()

    # ------------------------------------------------------------------
    # ISocialProvider — Utility
    # ------------------------------------------------------------------

    async def close(self) -> None:
        await self._client.aclose()
