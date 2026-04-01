"""Unit tests for TweAPI normalizer."""

from datetime import UTC

from app.providers.tweapi.normalizer import (
    _media_type,
    _parse_dt,
    normalize_credit_balance,
    normalize_tweet,
    normalize_user,
)
from app.providers.tweapi.types import (
    TweAPIAuthor,
    TweAPICreditBalance,
    TweAPIMediaItem,
    TweAPITweet,
)
from app.shared.types import CreditBalance, Post, UserInfo


class TestParseDt:
    def test_iso_with_z(self):
        dt = _parse_dt("2024-01-15T10:30:00Z")
        assert dt is not None
        assert dt.year == 2024
        assert dt.tzinfo is not None

    def test_iso_with_offset(self):
        dt = _parse_dt("2024-01-15T10:30:00+00:00")
        assert dt is not None
        assert dt.tzinfo is not None

    def test_none_input(self):
        assert _parse_dt(None) is None

    def test_empty_string(self):
        assert _parse_dt("") is None

    def test_invalid_string(self):
        assert _parse_dt("not-a-date") is None

    def test_naive_datetime_gets_utc(self):
        dt = _parse_dt("2024-01-15T10:30:00")
        assert dt is not None
        assert dt.tzinfo == UTC


class TestMediaType:
    def test_photo(self):
        assert _media_type("PHOTO") == "photo"

    def test_video(self):
        assert _media_type("VIDEO") == "video"

    def test_gif(self):
        assert _media_type("GIF") == "gif"

    def test_unknown_lowered(self):
        assert _media_type("AUDIO") == "audio"

    def test_case_insensitive(self):
        assert _media_type("Photo") == "photo"


class TestNormalizeUser:
    def test_basic_fields(self):
        author = TweAPIAuthor(
            id="123",
            userName="testuser",
            fullName="Test User",
            description="A bio",
            followersCount=100,
            followingsCount=50,
            statusesCount=500,
            isVerified=True,
            location="NYC",
            createdAt="2020-01-01T00:00:00Z",
        )
        result = normalize_user(author)
        assert isinstance(result, UserInfo)
        assert result.username == "testuser"
        assert result.display_name == "Test User"
        assert result.followers_count == 100
        assert result.following_count == 50
        assert result.is_verified is True
        assert result.location == "NYC"
        assert result.raw_json is not None

    def test_empty_fullname(self):
        author = TweAPIAuthor(userName="noname", fullName="")
        result = normalize_user(author)
        assert result.display_name is None


class TestNormalizeTweet:
    def test_basic_tweet(self):
        tweet = TweAPITweet(
            id="tweet1",
            fullText="Hello world",
            createdAt="2024-06-01T12:00:00Z",
            likeCount=10,
            retweetCount=5,
            replyCount=2,
            viewCount=100,
            tweetBy=TweAPIAuthor(userName="author1", fullName="Author One"),
        )
        result = normalize_tweet(tweet)
        assert isinstance(result, Post)
        assert result.platform_post_id == "tweet1"
        assert result.content == "Hello world"
        assert result.author.username == "author1"
        assert result.metrics.likes == 10
        assert result.metrics.views == 100
        assert result.is_retweet is False
        assert result.is_reply is False

    def test_tweet_with_media(self):
        tweet = TweAPITweet(
            id="tweet2",
            fullText="With media",
            tweetBy=TweAPIAuthor(userName="author"),
            media=[
                TweAPIMediaItem(
                    type="PHOTO",
                    url="https://img.com/1.jpg",
                    thumbnailUrl="https://img.com/1_thumb.jpg",
                ),
                TweAPIMediaItem(type="VIDEO", url="https://vid.com/1.mp4"),
            ],
        )
        result = normalize_tweet(tweet)
        assert len(result.media) == 2
        assert result.media[0].type == "photo"
        assert result.media[0].url == "https://img.com/1.jpg"
        assert result.media[1].type == "video"

    def test_tweet_with_no_author(self):
        tweet = TweAPITweet(id="tweet3", fullText="No author", tweetBy=None)
        result = normalize_tweet(tweet)
        assert result.author.username == ""

    def test_reply_detection(self):
        tweet = TweAPITweet(
            id="reply1",
            fullText="A reply",
            tweetBy=TweAPIAuthor(userName="replier"),
            replyTo="original_tweet_id",
        )
        result = normalize_tweet(tweet)
        assert result.is_reply is True
        assert result.reply_to_post_id == "original_tweet_id"

    def test_retweet_detection(self):
        rt = TweAPITweet(id="original", fullText="Original")
        tweet = TweAPITweet(
            id="rt1",
            fullText="RT content",
            tweetBy=TweAPIAuthor(userName="retweeter"),
            retweetedTweet=rt,
        )
        result = normalize_tweet(tweet)
        assert result.is_retweet is True

    def test_quoted_tweet(self):
        quoted = TweAPITweet(
            id="quoted1",
            fullText="Quoted text",
            tweetBy=TweAPIAuthor(userName="quotee"),
        )
        tweet = TweAPITweet(
            id="main1",
            fullText="Main text",
            tweetBy=TweAPIAuthor(userName="quoter"),
            quoted=quoted,
        )
        result = normalize_tweet(tweet)
        assert result.quoted_post is not None
        assert result.quoted_post.platform_post_id == "quoted1"
        assert result.quoted_post.content == "Quoted text"

    def test_media_without_url_excluded(self):
        tweet = TweAPITweet(
            id="t1",
            fullText="test",
            tweetBy=TweAPIAuthor(userName="u"),
            media=[
                TweAPIMediaItem(type="PHOTO", url=""),
                TweAPIMediaItem(type="PHOTO", url="https://real.jpg"),
            ],
        )
        result = normalize_tweet(tweet)
        assert len(result.media) == 1


class TestNormalizeCreditBalance:
    def test_basic(self):
        credits = TweAPICreditBalance(remaining=500, total=1000, expiresAt="2024-12-31T23:59:59Z")
        result = normalize_credit_balance(credits)
        assert isinstance(result, CreditBalance)
        assert result.remaining == 500
        assert result.total == 1000
        assert result.reset_at is not None
