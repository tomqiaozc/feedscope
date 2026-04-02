"""Normalize TwitterAPI.io raw responses into platform-agnostic shared types."""

from __future__ import annotations

from datetime import UTC, datetime

from app.providers.twitterapi.types import TAAuthor, TAFollowerUser, TATweet
from app.shared.types import Author, MediaItem, Post, PostMetrics, UserInfo


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        # TwitterAPI.io uses formats like "Wed Apr 01 17:31:59 +0000 2026"
        # or ISO format "2009-06-02T20:12:29.000000Z"
        if "T" in value:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        else:
            dt = datetime.strptime(value, "%a %b %d %H:%M:%S %z %Y")
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt
    except (ValueError, TypeError):
        return None


def normalize_user(author: TAAuthor) -> UserInfo:
    return UserInfo(
        username=author.userName,
        display_name=author.name or None,
        description=author.description,
        profile_image_url=author.profilePicture,
        followers_count=author.followers,
        following_count=author.following,
        tweet_count=author.statusesCount,
        is_verified=author.isBlueVerified or author.isVerified,
        location=author.location,
        website=author.url,
        joined_at=_parse_dt(author.createdAt),
        raw_json=author.model_dump(),
    )


def normalize_follower_user(user: TAFollowerUser) -> UserInfo:
    return UserInfo(
        username=user.userName or user.screen_name,
        display_name=user.name or None,
        description=user.description,
        profile_image_url=user.profile_image_url_https,
        followers_count=user.followers_count,
        following_count=user.following_count or user.friends_count,
        tweet_count=user.statuses_count,
        is_verified=user.verified,
        location=user.location,
        joined_at=_parse_dt(user.created_at),
        raw_json=user.model_dump(),
    )


def normalize_tweet(tweet: TATweet) -> Post:
    author = Author(
        username=tweet.author.userName if tweet.author else "",
        display_name=tweet.author.name if tweet.author else None,
        profile_image_url=tweet.author.profilePicture if tweet.author else None,
        is_verified=(tweet.author.isBlueVerified or tweet.author.isVerified) if tweet.author else False,
    )

    media: list[MediaItem] = []
    if tweet.extendedEntities and tweet.extendedEntities.media:
        for m in tweet.extendedEntities.media:
            url = m.media_url_https or m.url or m.expanded_url
            if url:
                media.append(MediaItem(
                    type=_media_type(m.type),
                    url=url,
                    preview_url=m.media_url_https,
                ))

    metrics = PostMetrics(
        likes=tweet.likeCount,
        retweets=tweet.retweetCount,
        replies=tweet.replyCount,
        views=tweet.viewCount or 0,
        bookmarks=tweet.bookmarkCount,
        quotes=tweet.quoteCount,
    )

    quoted_post = normalize_tweet(tweet.quoted_tweet) if tweet.quoted_tweet else None
    is_retweet = tweet.retweeted_tweet is not None

    return Post(
        platform_post_id=tweet.id,
        author=author,
        content=tweet.text,
        posted_at=_parse_dt(tweet.createdAt),
        metrics=metrics,
        media=media,
        quoted_post=quoted_post,
        is_retweet=is_retweet,
        is_reply=tweet.isReply,
        reply_to_post_id=tweet.inReplyToId,
        conversation_id=tweet.conversationId,
        language=tweet.lang,
        raw_json=tweet.model_dump(),
    )


def _media_type(raw_type: str) -> str:
    mapping = {"photo": "photo", "video": "video", "animated_gif": "gif"}
    return mapping.get(raw_type.lower(), raw_type.lower())
