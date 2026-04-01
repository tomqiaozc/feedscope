"""Normalize TweAPI raw responses into platform-agnostic shared types."""

from __future__ import annotations

from datetime import UTC, datetime

from app.providers.tweapi.types import (
    TweAPIAnalytics,
    TweAPIAuthor,
    TweAPICreditBalance,
    TweAPIInboxItem,
    TweAPIMessage,
    TweAPITweet,
)
from app.shared.types import Author, CreditBalance, MediaItem, Post, PostMetrics, UserInfo


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt
    except (ValueError, TypeError):
        return None


def _media_type(raw_type: str) -> str:
    mapping = {"PHOTO": "photo", "VIDEO": "video", "GIF": "gif"}
    return mapping.get(raw_type.upper(), raw_type.lower())


def normalize_user(author: TweAPIAuthor) -> UserInfo:
    return UserInfo(
        username=author.userName,
        display_name=author.fullName or None,
        description=author.description,
        profile_image_url=author.profileImage or None,
        followers_count=author.followersCount,
        following_count=author.followingsCount,
        tweet_count=author.statusesCount,
        is_verified=author.isVerified,
        location=author.location,
        joined_at=_parse_dt(author.createdAt),
        raw_json=author.model_dump(),
    )


def normalize_tweet(tweet: TweAPITweet) -> Post:
    author = Author(
        username=tweet.tweetBy.userName if tweet.tweetBy else "",
        display_name=tweet.tweetBy.fullName if tweet.tweetBy else None,
        profile_image_url=tweet.tweetBy.profileImage if tweet.tweetBy else None,
        is_verified=tweet.tweetBy.isVerified if tweet.tweetBy else False,
    )

    media = [
        MediaItem(
            type=_media_type(m.type),
            url=m.url,
            preview_url=m.thumbnailUrl,
        )
        for m in tweet.media
        if m.url
    ]

    metrics = PostMetrics(
        likes=tweet.likeCount,
        retweets=tweet.retweetCount,
        replies=tweet.replyCount,
        views=tweet.viewCount or 0,
        bookmarks=tweet.bookmarkCount,
        quotes=tweet.quoteCount,
    )

    quoted_post = normalize_tweet(tweet.quoted) if tweet.quoted else None
    is_retweet = tweet.retweetedTweet is not None

    return Post(
        platform_post_id=tweet.id,
        author=author,
        content=tweet.fullText,
        posted_at=_parse_dt(tweet.createdAt),
        metrics=metrics,
        media=media,
        quoted_post=quoted_post,
        is_retweet=is_retweet,
        is_reply=tweet.replyTo is not None,
        reply_to_post_id=tweet.replyTo,
        conversation_id=tweet.conversationId,
        language=tweet.lang,
        raw_json=tweet.model_dump(),
    )


def normalize_inbox_item(item: TweAPIInboxItem) -> dict:
    return {
        "conversation_id": item.conversationId,
        "last_message": normalize_message(item.lastMessage) if item.lastMessage else None,
        "participants": [normalize_user(p).model_dump() for p in item.participants],
        "unread_count": item.unreadCount or 0,
    }


def normalize_message(msg: TweAPIMessage) -> dict:
    return {
        "id": msg.id,
        "text": msg.text,
        "sender_id": msg.senderId,
        "recipient_id": msg.recipientId,
        "created_at": msg.createdAt,
        "media_urls": msg.mediaUrls,
    }


def normalize_analytics(analytics: TweAPIAnalytics) -> dict:
    return {
        "created_at": analytics.createdAt,
        "followers": analytics.followers,
        "verified_followers": analytics.verifiedFollowers,
        "impressions": analytics.impressions,
        "profile_visits": analytics.profileVisits,
        "engagements": analytics.engagements,
        "follows": analytics.follows,
        "replies": analytics.replies,
        "likes": analytics.likes,
        "retweets": analytics.retweets,
        "bookmarks": analytics.bookmarks,
        "shares": analytics.shares,
    }


def normalize_credit_balance(credits: TweAPICreditBalance) -> CreditBalance:
    return CreditBalance(
        remaining=credits.remaining,
        total=credits.total,
        reset_at=_parse_dt(credits.expiresAt),
    )
