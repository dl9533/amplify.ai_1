"""Configuration module with Pydantic Settings for the Discovery service.

This module provides centralized configuration management using pydantic-settings,
loading values from environment variables with sensible defaults.
"""
from functools import lru_cache
from urllib.parse import quote_plus

from pydantic import SecretStr, computed_field
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
    postgres_password: SecretStr = SecretStr("discovery_dev")
    postgres_db: str = "discovery"

    # Redis configuration
    redis_url: str = "redis://localhost:6379/0"

    # S3 storage configuration
    s3_endpoint_url: str | None = None
    s3_bucket: str = "discovery-uploads"
    aws_access_key_id: str | None = None
    aws_secret_access_key: SecretStr | None = None
    aws_region: str = "us-east-1"

    # O*NET API configuration
    onet_api_key: SecretStr = SecretStr("")
    onet_api_base_url: str = "https://api-v2.onetcenter.org/"

    # Anthropic configuration
    anthropic_api_key: SecretStr = SecretStr("")
    anthropic_model: str = "claude-sonnet-4-20250514"

    # Application settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False
    log_level: str = "INFO"

    # CORS configuration
    cors_allowed_origins: str = "http://localhost:3000"
    cors_allow_credentials: bool = True
    cors_allowed_methods: str = "GET,POST,PUT,DELETE,OPTIONS"
    cors_allowed_headers: str = "Authorization,Content-Type,X-Request-ID"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS allowed origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_allowed_origins.split(",")]

    @property
    def cors_methods_list(self) -> list[str]:
        """Parse CORS allowed methods from comma-separated string."""
        return [method.strip() for method in self.cors_allowed_methods.split(",")]

    @property
    def cors_headers_list(self) -> list[str]:
        """Parse CORS allowed headers from comma-separated string."""
        return [header.strip() for header in self.cors_allowed_headers.split(",")]

    @computed_field(repr=False)  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> str:
        """Build PostgreSQL connection URL with asyncpg driver.

        Returns:
            PostgreSQL connection string in the format:
            postgresql+asyncpg://user:password@host:port/database
        """
        encoded_password = quote_plus(self.postgres_password.get_secret_value())
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{encoded_password}"
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
