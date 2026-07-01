import os
from typing import List, Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Settings class loading environment configurations.
    Uses Pydantic validation rules.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Core configs
    APP_ENV: Literal["development", "testing", "production"] = "development"
    APP_NAME: str = "CloudPilot AI"
    DEBUG: bool = False
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Security
    JWT_SECRET: str = Field(..., min_length=32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ENCRYPTION_KEY: str = Field(..., min_length=44)  # KEK (32-bytes base64 encoded)

    # Database
    DATABASE_URL: str
    REDIS_URL: str

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    CHAT_LIMIT_PER_MINUTE: int = 20
    AUTH_LIMIT_PER_MINUTE: int = 5

    # Logging
    LOG_LEVEL: str = "info"
    LOG_FORMAT: Literal["json", "console"] = "json"
    LOG_FILE_PATH: str = "logs/cloudpilot.log"

    # CORS Allowed Origins
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if v.startswith("sqlite+aiosqlite://"):
            return v
        if not v.startswith("postgresql+asyncpg://"):
            # Auto-covert standard postgresql driver to asyncpg
            if v.startswith("postgresql://"):
                return v.replace("postgresql://", "postgresql+asyncpg://", 1)
            raise ValueError("Database URL must be a valid PostgreSQL connection using asyncpg.")
        return v

    @field_validator("REDIS_URL")
    @classmethod
    def validate_redis_url(cls, v: str) -> str:
        if v.startswith("mock://"):
            return v
        if not v.startswith("redis://") and not v.startswith("rediss://"):
            raise ValueError("Redis URL must be a valid redis:// or rediss:// connection.")
        return v


# Instantiate settings instance
settings = Settings()

# Global Redis Mocking when real Redis is unavailable
try:
    import redis.asyncio
    import fakeredis.aioredis
    import redis as sync_redis

    _original_from_url = redis.asyncio.from_url
    _redis_mode = None

    def mocked_from_url(*args, **kwargs):
        global _redis_mode
        if _redis_mode == "fake":
            return fakeredis.aioredis.FakeRedis()
        elif _redis_mode == "real":
            return _original_from_url(*args, **kwargs)

        url = args[0] if args else kwargs.get("url", settings.REDIS_URL)
        if url.startswith("mock://"):
            _redis_mode = "fake"
            return fakeredis.aioredis.FakeRedis()

        try:
            # Quick sync ping check
            client = sync_redis.from_url(url, socket_timeout=0.2, socket_connect_timeout=0.2)
            client.ping()
            _redis_mode = "real"
            return _original_from_url(*args, **kwargs)
        except Exception:
            _redis_mode = "fake"
            return fakeredis.aioredis.FakeRedis()

    redis.asyncio.from_url = mocked_from_url
except ImportError:
    pass

