from functools import lru_cache
from typing import Literal

from pydantic import PostgresDsn, RedisDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str = "CLARA"
    debug: bool = False
    secret_key: SecretStr
    encryption_key: str = ""

    database_url: PostgresDsn
    pool_size: int = 5
    pool_max_overflow: int = 10
    redis_url: RedisDsn = RedisDsn("redis://localhost:6379/0")

    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30
    cookie_domain: str | None = None
    cookie_secure: bool = True
    cookie_httponly: bool = True
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"

    cors_origins: list[str] = []
    frontend_url: str = "http://localhost:5173"

    storage_path: str = "./uploads"
    git_sync_work_dir: str = "./git_sync_repos"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: SecretStr | None = None
    email_from: str = "noreply@clara.local"

    max_body_size: int = 1_048_576  # 1 MB for JSON
    max_upload_size: int = 52_428_800  # 50 MB for files

    @property
    def async_database_url(self) -> str:
        return str(self.database_url).replace(
            "postgresql://", "postgresql+asyncpg://"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
