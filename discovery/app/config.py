"""Configuration module with Pydantic Settings for the Discovery service.

This module provides centralized configuration management using pydantic-settings,
loading values from environment variables with sensible defaults.
"""
from functools import lru_cache

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All configuration values can be overridden by setting the corresponding
    environment variable (case-insensitive).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database configuration
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "discovery"
    postgres_password: str = "discovery_dev"
    postgres_db: str = "discovery"

    # Redis configuration
    redis_url: str = "redis://localhost:6379/0"

    # S3 storage configuration
    s3_endpoint_url: str | None = None
    s3_bucket: str = "discovery-uploads"
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_region: str = "us-east-1"

    # O*NET API configuration
    onet_api_key: str = ""
    onet_api_base_url: str = "https://services.onetcenter.org/ws/"

    # Anthropic configuration
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"

    # Application settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False
    log_level: str = "INFO"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> str:
        """Build PostgreSQL connection URL with asyncpg driver.

        Returns:
            PostgreSQL connection string in the format:
            postgresql+asyncpg://user:password@host:port/database
        """
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    """Get application settings instance with caching.

    Uses lru_cache to ensure only one Settings instance is created
    (singleton pattern), improving performance and consistency.

    Returns:
        The cached Settings instance.
    """
    return Settings()
