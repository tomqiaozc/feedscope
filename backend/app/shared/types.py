from datetime import datetime

from pydantic import BaseModel


class Author(BaseModel):
    username: str
    display_name: str | None = None
    profile_image_url: str | None = None
    is_verified: bool = False


class MediaItem(BaseModel):
    type: str  # "photo", "video", "gif"
    url: str
    preview_url: str | None = None
    width: int | None = None
    height: int | None = None


class PostMetrics(BaseModel):
    likes: int = 0
    retweets: int = 0
    replies: int = 0
    views: int = 0
    bookmarks: int = 0
    quotes: int = 0


class Post(BaseModel):
    platform_post_id: str
    author: Author
    content: str
    posted_at: datetime | None = None
    metrics: PostMetrics = PostMetrics()
    media: list[MediaItem] = []
    quoted_post: "Post | None" = None
    is_retweet: bool = False
    is_reply: bool = False
    reply_to_post_id: str | None = None
    conversation_id: str | None = None
    language: str | None = None
    raw_json: dict | None = None


class UserInfo(BaseModel):
    username: str
    display_name: str | None = None
    description: str | None = None
    profile_image_url: str | None = None
    followers_count: int = 0
    following_count: int = 0
    tweet_count: int = 0
    is_verified: bool = False
    location: str | None = None
    website: str | None = None
    joined_at: datetime | None = None
    raw_json: dict | None = None


class CreditBalance(BaseModel):
    remaining: int = 0
    total: int = 0
    reset_at: datetime | None = None
