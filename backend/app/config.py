import json

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://feedscope:feedscope@localhost:5432/feedscope"
    cors_origins: str = '["http://localhost:3000"]'
    environment: str = "development"
    tweapi_base_url: str = "https://api.tweapi.io"
    tweapi_timeout_ms: int = 30000
    twitter_provider: str = "twitterapi"  # "tweapi" or "twitterapi"
    twitterapi_base_url: str = "https://api.twitterapi.io"
    twitterapi_timeout_ms: int = 30000
    mock_provider: bool = False
    e2e_skip_auth: bool = False

    @property
    def cors_origins_list(self) -> list[str]:
        v = self.cors_origins
        if v.startswith("["):
            return json.loads(v)
        return [origin.strip() for origin in v.split(",") if origin.strip()]

    @property
    def effective_e2e_skip_auth(self) -> bool:
        if self.environment == "production":
            return False
        return self.e2e_skip_auth

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
