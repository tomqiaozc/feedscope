from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://feedscope:feedscope@localhost:5432/feedscope"
    cors_origins: list[str] = ["http://localhost:3000"]
    environment: str = "development"
    tweapi_base_url: str = "https://api.tweapi.io"
    tweapi_timeout_ms: int = 30000
    mock_provider: bool = False
    e2e_skip_auth: bool = False

    @property
    def effective_e2e_skip_auth(self) -> bool:
        if self.environment == "production":
            return False
        return self.e2e_skip_auth

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
