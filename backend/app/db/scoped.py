from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repos.credentials_repo import CredentialsRepo
from app.db.repos.fetch_log_repo import FetchLogRepo
from app.db.repos.group_member_repo import GroupMemberRepo
from app.db.repos.group_repo import GroupRepo
from app.db.repos.member_repo import MemberRepo
from app.db.repos.post_repo import PostRepo
from app.db.repos.settings_repo import SettingsRepo
from app.db.repos.tag_repo import TagRepo
from app.db.repos.usage_daily_repo import UsageDailyRepo
from app.db.repos.watchlist_repo import WatchlistRepo
from app.db.repos.watchlist_settings_repo import WatchlistSettingsRepo
from app.db.repos.webhook_repo import WebhookRepo
from app.db.repos.webhook_usage_repo import WebhookUsageRepo


class ScopedDB:
    def __init__(self, user_id: str, session: AsyncSession):
        self.user_id = user_id
        self.session = session
        self.watchlists = WatchlistRepo(user_id, session)
        self.members = MemberRepo(user_id, session)
        self.tags = TagRepo(user_id, session)
        self.posts = PostRepo(user_id, session)
        self.fetch_logs = FetchLogRepo(user_id, session)
        self.groups = GroupRepo(user_id, session)
        self.group_members = GroupMemberRepo(user_id, session)
        self.settings = SettingsRepo(user_id, session)
        self.credentials = CredentialsRepo(user_id, session)
        self.webhooks = WebhookRepo(user_id, session)
        self.webhook_usage = WebhookUsageRepo(user_id, session)
        self.usage_daily = UsageDailyRepo(user_id, session)
        self.watchlist_settings = WatchlistSettingsRepo(user_id, session)
