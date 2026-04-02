"""Raw TwitterAPI.io response models.

Uses extra="ignore" so new fields from the API don't break parsing.
"""

from __future__ import annotations

from pydantic import BaseModel


class TAAuthor(BaseModel, extra="ignore"):
    id: str = ""
    name: str = ""
    userName: str = ""
    description: str | None = None
    location: str | None = None
    profilePicture: str | None = None
    coverPicture: str | None = None
    followers: int = 0
    following: int = 0
    statusesCount: int = 0
    favouritesCount: int = 0
    isVerified: bool = False
    isBlueVerified: bool = False
    createdAt: str | None = None
    url: str | None = None


class TAMediaItem(BaseModel, extra="ignore"):
    type: str = ""  # "photo", "video", "animated_gif"
    url: str | None = None
    media_url_https: str | None = None
    expanded_url: str | None = None


class TAExtendedEntities(BaseModel, extra="ignore"):
    media: list[TAMediaItem] = []


class TATweet(BaseModel, extra="ignore"):
    id: str = ""
    text: str = ""
    url: str | None = None
    createdAt: str | None = None
    lang: str | None = None
    retweetCount: int = 0
    replyCount: int = 0
    likeCount: int = 0
    quoteCount: int = 0
    viewCount: int = 0
    bookmarkCount: int = 0
    isReply: bool = False
    inReplyToId: str | None = None
    conversationId: str | None = None
    author: TAAuthor | None = None
    extendedEntities: TAExtendedEntities | None = None
    quoted_tweet: TATweet | None = None
    retweeted_tweet: TATweet | None = None


# --- Response envelopes ---


class TAUserInfoResponse(BaseModel, extra="ignore"):
    status: str = ""
    msg: str = ""
    data: TAAuthor | None = None


class TATweetListData(BaseModel, extra="ignore"):
    pin_tweet: TATweet | None = None
    tweets: list[TATweet] = []


class TAUserTweetsResponse(BaseModel, extra="ignore"):
    status: str = ""
    code: int = 0
    msg: str = ""
    data: TATweetListData | None = None


class TASearchResponse(BaseModel, extra="ignore"):
    tweets: list[TATweet] = []
    has_next_page: bool = False
    next_cursor: str | None = None


class TAFollowersResponse(BaseModel, extra="ignore"):
    followers: list[TAFollowerUser] = []
    has_next_page: bool = False
    next_cursor: str | None = None


class TAFollowingResponse(BaseModel, extra="ignore"):
    following: list[TAFollowerUser] = []
    has_next_page: bool = False
    next_cursor: str | None = None


class TAFollowerUser(BaseModel, extra="ignore"):
    id: str = ""
    name: str = ""
    screen_name: str = ""
    userName: str | None = None
    description: str | None = None
    location: str | None = None
    followers_count: int = 0
    following_count: int = 0
    friends_count: int = 0
    statuses_count: int = 0
    profile_image_url_https: str | None = None
    profile_banner_url: str | None = None
    verified: bool = False
    created_at: str | None = None


class TATweetsById(BaseModel, extra="ignore"):
    tweets: list[TATweet] = []


# Fix forward reference
TAFollowersResponse.model_rebuild()
TAFollowingResponse.model_rebuild()
