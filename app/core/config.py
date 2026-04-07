from functools import lru_cache

from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


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

    # Dimensão dos embeddings — manter alinhado a app.core.constants.DEFAULT_EMBEDDING_DIMENSIONS
    embedding_dimensions: int = 384

    # Geração automática (POST .../embedding/generate) — opcional
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_embedding_model: str = "text-embedding-3-small"


@lru_cache
def get_settings() -> Settings:
    return Settings()
