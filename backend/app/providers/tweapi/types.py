"""Raw TweAPI.io response models.

Uses extra="ignore" per blueprint risk R-7 (response shapes may change).
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class TweAPIMediaItem(BaseModel, extra="ignore"):
    id: str | None = None
    type: str = ""  # "PHOTO", "VIDEO", "GIF"
    url: str = ""
    thumbnailUrl: str | None = None


class TweAPIAuthor(BaseModel, extra="ignore"):
    id: str = ""
    userName: str = ""
    fullName: str = ""
    description: str | None = None
    location: str | None = None
    profileImage: str = ""
    profileBanner: str | None = None
    followersCount: int = 0
    followingsCount: int = 0
    statusesCount: int = 0
    likeCount: int = 0
    isVerified: bool = False
    createdAt: str | None = None
    pinnedTweet: str | None = None


class TweAPIEntities(BaseModel, extra="ignore"):
    hashtags: list[str] = []
    mentionedUsers: list[str] = []
    urls: list[str] = []


class TweAPITweet(BaseModel, extra="ignore"):
    id: str = ""
    url: str = ""
    fullText: str = ""
    createdAt: str | None = None
    lang: str | None = None
    bookmarkCount: int = 0
    likeCount: int = 0
    retweetCount: int = 0
    replyCount: int = 0
    quoteCount: int = 0
    viewCount: int | None = None
    conversationId: str | None = None
    tweetBy: TweAPIAuthor | None = None
    entities: TweAPIEntities = TweAPIEntities()
    media: list[TweAPIMediaItem] = []
    quoted: TweAPITweet | None = None
    replyTo: str | None = None
    retweetedTweet: TweAPITweet | None = None


class TweAPIList(BaseModel, extra="ignore"):
    id: str = ""
    name: str = ""
    description: str | None = None
    memberCount: int = 0
    subscriberCount: int = 0
    createdAt: str | None = None
    createdBy: str | None = None
    isFollowing: bool | None = None
    isMember: bool | None = None


class TweAPIAnalytics(BaseModel, extra="ignore"):
    createdAt: str | None = None
    followers: int = 0
    verifiedFollowers: int | None = None
    impressions: int = 0
    profileVisits: int = 0
    engagements: int = 0
    follows: int | None = None
    replies: int | None = None
    likes: int | None = None
    retweets: int | None = None
    bookmarks: int | None = None
    shares: int | None = None


class TweAPIMessage(BaseModel, extra="ignore"):
    id: str = ""
    text: str = ""
    senderId: str = ""
    recipientId: str = ""
    createdAt: str | None = None
    mediaUrls: list[str] = []


class TweAPIInboxItem(BaseModel, extra="ignore"):
    conversationId: str = ""
    lastMessage: TweAPIMessage | None = None
    participants: list[TweAPIAuthor] = []
    unreadCount: int | None = None


class TweAPICreditBalance(BaseModel, extra="ignore"):
    remaining: int = 0
    total: int = 0
    expiresAt: str | None = None


# --- Envelope wrappers ---


class TweAPIEnvelope(BaseModel, extra="ignore"):
    code: int = 0
    msg: str = ""


class TweAPITweetList(TweAPIEnvelope):
    data: TweAPITweetListData = Field(default_factory=lambda: TweAPITweetListData())


class TweAPITweetListData(BaseModel, extra="ignore"):
    model_config = {"populate_by_name": True}
    items: list[TweAPITweet] = Field(default_factory=lambda: [], alias="list")
    next: str | None = None


class TweAPIAuthorList(TweAPIEnvelope):
    data: TweAPIAuthorListData = Field(default_factory=lambda: TweAPIAuthorListData())


class TweAPIAuthorListData(BaseModel, extra="ignore"):
    model_config = {"populate_by_name": True}
    items: list[TweAPIAuthor] = Field(default_factory=lambda: [], alias="list")
    next: str | None = None


class TweAPISingleTweet(TweAPIEnvelope):
    data: TweAPITweet | None = None


class TweAPISingleAuthor(TweAPIEnvelope):
    data: TweAPIAuthor | None = None


class TweAPIListList(TweAPIEnvelope):
    data: TweAPIListListData = Field(default_factory=lambda: TweAPIListListData())


class TweAPIListListData(BaseModel, extra="ignore"):
    model_config = {"populate_by_name": True}
    items: list[TweAPIList] = Field(default_factory=lambda: [], alias="list")
    next: str | None = None


class TweAPIAnalyticsResponse(TweAPIEnvelope):
    data: TweAPIAnalytics | None = None


class TweAPICreditResponse(TweAPIEnvelope):
    data: TweAPICreditBalance | None = None


class TweAPIInboxList(TweAPIEnvelope):
    data: TweAPIInboxListData = Field(default_factory=lambda: TweAPIInboxListData())


class TweAPIInboxListData(BaseModel, extra="ignore"):
    model_config = {"populate_by_name": True}
    items: list[TweAPIInboxItem] = Field(default_factory=lambda: [], alias="list")
    next: str | None = None


class TweAPIConversationData(BaseModel, extra="ignore"):
    conversationId: str = ""
    messages: list[TweAPIMessage] = []
    participants: list[TweAPIAuthor] = []


class TweAPIConversationResponse(TweAPIEnvelope):
    data: TweAPIConversationData | None = None
