"""Mock provider for testing and development."""

from __future__ import annotations

from datetime import UTC, datetime

from app.providers.base import AuthRequiredError
from app.shared.types import Author, CreditBalance, MediaItem, Post, PostMetrics, UserInfo

_NOW = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)


def _mock_author(username: str = "mockuser") -> Author:
    return Author(
        username=username,
        display_name=f"Mock {username.title()}",
        profile_image_url="https://example.com/avatar.jpg",
        is_verified=False,
    )


def _mock_post(idx: int = 1, username: str = "mockuser") -> Post:
    return Post(
        platform_post_id=f"mock-{idx}",
        author=_mock_author(username),
        content=f"This is mock tweet #{idx} from @{username}",
        posted_at=_NOW,
        metrics=PostMetrics(likes=idx * 10, retweets=idx * 2, replies=idx, views=idx * 100),
        media=[MediaItem(type="photo", url=f"https://example.com/img{idx}.jpg")]
        if idx % 3 == 0
        else [],
    )


def _mock_user(username: str = "mockuser") -> UserInfo:
    return UserInfo(
        username=username,
        display_name=f"Mock {username.title()}",
        description=f"Mock profile for {username}",
        profile_image_url="https://example.com/avatar.jpg",
        followers_count=1000,
        following_count=500,
        tweet_count=2500,
        is_verified=False,
        location="Mock City",
        joined_at=_NOW,
    )


def _mock_posts(count: int, username: str = "mockuser") -> list[Post]:
    return [_mock_post(i, username) for i in range(1, count + 1)]


class MockProvider:
    """In-memory provider returning deterministic test data."""

    def __init__(self, cookie: str | None = None) -> None:
        self._cookie = cookie

    def _require_cookie(self) -> str:
        if not self._cookie:
            raise AuthRequiredError("Cookie required for this endpoint")
        return self._cookie

    # --- User info ---
    async def fetch_user_info(self, username: str) -> UserInfo:
        return _mock_user(username)

    # --- User content ---
    async def fetch_user_tweets(
        self, username: str, *, count: int = 20, cursor: str | None = None
    ) -> list[Post]:
        return _mock_posts(min(count, 5), username)

    async def fetch_user_timeline(
        self, username: str, *, count: int = 20, cursor: str | None = None
    ) -> list[Post]:
        return _mock_posts(min(count, 5), username)

    async def fetch_user_replies(
        self, username: str, *, count: int = 20, cursor: str | None = None
    ) -> list[Post]:
        posts = _mock_posts(min(count, 3), username)
        for p in posts:
            p.is_reply = True
            p.reply_to_post_id = "mock-parent"
        return posts

    async def fetch_user_highlights(
        self, username: str, *, count: int = 20, cursor: str | None = None
    ) -> list[Post]:
        return _mock_posts(min(count, 2), username)

    # --- Social graph ---
    async def fetch_followers(
        self, username: str, *, count: int = 20, cursor: str | None = None
    ) -> list[UserInfo]:
        return [_mock_user(f"follower{i}") for i in range(1, min(count, 5) + 1)]

    async def fetch_following(
        self, username: str, *, count: int = 20, cursor: str | None = None
    ) -> list[UserInfo]:
        return [_mock_user(f"following{i}") for i in range(1, min(count, 5) + 1)]

    # --- Search ---
    async def search_tweets(
        self, query: str, *, count: int = 20, cursor: str | None = None
    ) -> list[Post]:
        posts = _mock_posts(min(count, 3))
        for p in posts:
            p.content = f"[search: {query}] {p.content}"
        return posts

    # --- Single tweet ---
    async def fetch_tweet_details(self, tweet_id: str) -> Post:
        post = _mock_post(1)
        post.platform_post_id = tweet_id
        return post

    async def fetch_tweet_replies(
        self, tweet_id: str, *, count: int = 20, cursor: str | None = None
    ) -> list[Post]:
        posts = _mock_posts(min(count, 3))
        for p in posts:
            p.is_reply = True
            p.reply_to_post_id = tweet_id
        return posts

    # --- Authenticated (cookie required) ---
    async def fetch_bookmarks(self, *, count: int = 20, cursor: str | None = None) -> list[Post]:
        self._require_cookie()
        return _mock_posts(min(count, 3))

    async def fetch_likes(
        self, username: str, *, count: int = 20, cursor: str | None = None
    ) -> list[Post]:
        self._require_cookie()
        return _mock_posts(min(count, 3), username)

    # --- Lists ---
    async def fetch_lists(self, username: str) -> list[dict]:
        self._require_cookie()
        return [
            {"id": "list-1", "name": "Mock List", "member_count": 10, "subscriber_count": 5},
        ]

    async def fetch_list_members(
        self, list_id: str, *, count: int = 20, cursor: str | None = None
    ) -> list[UserInfo]:
        return [_mock_user(f"member{i}") for i in range(1, min(count, 3) + 1)]

    async def fetch_list_tweets(
        self, list_id: str, *, count: int = 20, cursor: str | None = None
    ) -> list[Post]:
        return _mock_posts(min(count, 3))

    # --- DMs / Inbox ---
    async def fetch_inbox(self, *, cursor: str | None = None) -> list[dict]:
        self._require_cookie()
        return [
            {
                "conversation_id": "conv-1",
                "last_message": {
                    "id": "msg-1",
                    "text": "Hello!",
                    "sender_id": "u1",
                    "recipient_id": "u2",
                    "created_at": _NOW.isoformat(),
                    "media_urls": [],
                },
                "participants": [
                    _mock_user("user1").model_dump(),
                    _mock_user("user2").model_dump(),
                ],
                "unread_count": 1,
            }
        ]

    async def fetch_messages(
        self, conversation_id: str, *, cursor: str | None = None
    ) -> list[dict]:
        self._require_cookie()
        return [
            {
                "id": f"msg-{i}",
                "text": f"Message {i}",
                "sender_id": "u1",
                "recipient_id": "u2",
                "created_at": _NOW.isoformat(),
                "media_urls": [],
            }
            for i in range(1, 4)
        ]

    # --- Analytics ---
    async def fetch_user_analytics(self, username: str) -> dict:
        self._require_cookie()
        return {
            "followers": 1000,
            "impressions": 50000,
            "engagements": 2500,
            "profile_visits": 300,
        }

    # --- Credits ---
    async def fetch_credits(self) -> CreditBalance:
        return CreditBalance(remaining=900, total=1000)

    # --- Utility ---
    async def close(self) -> None:
        pass
