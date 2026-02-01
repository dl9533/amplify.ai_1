"""Discovery API configuration using Pydantic Settings."""

from functools import cached_property

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Environment
    environment: str = "development"

    # Database settings
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "discovery"
    postgres_password: str = "discovery_dev"
    postgres_db: str = "discovery"

    # Redis settings
    redis_url: str = "redis://localhost:6379/0"

    # S3 storage settings
    s3_endpoint_url: str | None = None
    s3_bucket: str = "discovery-uploads"
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_region: str = "us-east-1"

    # O*NET API settings
    onet_api_username: str = ""
    onet_api_password: str = ""
    onet_api_base_url: str = "https://services.onetcenter.org/ws/"

    # Application settings
    api_host: str = "0.0.0.0"
    api_port: int = 8001
    debug: bool = False
    log_level: str = "INFO"

    @computed_field  # type: ignore[prop-decorator]
    @cached_property
    def database_url(self) -> str:
        """Build PostgreSQL connection URL."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


# Singleton instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings instance."""
    return settings
