from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.constants import DEFAULT_EMBEDDING_DIMENSIONS


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "fastapi-clean"
    debug: bool = False
    api_prefix: str = "/api/v1"

    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://app:app@localhost:5432/app",
    )

    secret_key: str = "change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    redis_url: RedisDsn = Field(default="redis://localhost:6379/0")

    log_level: str = "INFO"
    metrics_enabled: bool = True

    embedding_dimensions: int = DEFAULT_EMBEDDING_DIMENSIONS

    # dummy: teste PGVector. local: Sentence-Transformers. openai: API paga.
    embedding_provider: Literal["dummy", "local", "openai"] = "dummy"
    local_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_embedding_model: str = "text-embedding-3-small"


@lru_cache
def get_settings() -> Settings:
    return Settings()
