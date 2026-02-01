"""Tests for configuration module with pydantic-settings."""
import os
from functools import lru_cache
from unittest.mock import patch

import pytest


class TestSettingsFromEnvironment:
    """Tests for loading settings from environment variables."""

    def test_settings_loads_database_config_from_env(self):
        """Settings should load database configuration from environment variables."""
        env_vars = {
            "POSTGRES_HOST": "db.example.com",
            "POSTGRES_PORT": "5433",
            "POSTGRES_USER": "test_user",
            "POSTGRES_PASSWORD": "test_pass",
            "POSTGRES_DB": "test_db",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            # Clear any cached settings
            from app.config import get_settings
            get_settings.cache_clear()

            settings = get_settings()

            assert settings.postgres_host == "db.example.com"
            assert settings.postgres_port == 5433
            assert settings.postgres_user == "test_user"
            assert settings.postgres_password == "test_pass"
            assert settings.postgres_db == "test_db"

    def test_settings_loads_redis_config_from_env(self):
        """Settings should load Redis configuration from environment variables."""
        env_vars = {
            "REDIS_URL": "redis://redis.example.com:6380/1",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            from app.config import get_settings
            get_settings.cache_clear()

            settings = get_settings()

            assert settings.redis_url == "redis://redis.example.com:6380/1"

    def test_settings_loads_s3_config_from_env(self):
        """Settings should load S3 configuration from environment variables."""
        env_vars = {
            "S3_ENDPOINT_URL": "http://minio:9000",
            "S3_BUCKET": "test-bucket",
            "AWS_ACCESS_KEY_ID": "test_access_key",
            "AWS_SECRET_ACCESS_KEY": "test_secret_key",
            "AWS_REGION": "eu-west-1",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            from app.config import get_settings
            get_settings.cache_clear()

            settings = get_settings()

            assert settings.s3_endpoint_url == "http://minio:9000"
            assert settings.s3_bucket == "test-bucket"
            assert settings.aws_access_key_id == "test_access_key"
            assert settings.aws_secret_access_key == "test_secret_key"
            assert settings.aws_region == "eu-west-1"

    def test_settings_loads_onet_config_from_env(self):
        """Settings should load O*NET API configuration from environment variables."""
        env_vars = {
            "ONET_API_KEY": "onet_test_key_12345",
            "ONET_API_BASE_URL": "https://custom.onet.org/api/",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            from app.config import get_settings
            get_settings.cache_clear()

            settings = get_settings()

            assert settings.onet_api_key == "onet_test_key_12345"
            assert settings.onet_api_base_url == "https://custom.onet.org/api/"

    def test_settings_loads_anthropic_config_from_env(self):
        """Settings should load Anthropic configuration from environment variables."""
        env_vars = {
            "ANTHROPIC_API_KEY": "sk-ant-test-key",
            "ANTHROPIC_MODEL": "claude-opus-4-20250514",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            from app.config import get_settings
            get_settings.cache_clear()

            settings = get_settings()

            assert settings.anthropic_api_key == "sk-ant-test-key"
            assert settings.anthropic_model == "claude-opus-4-20250514"

    def test_settings_loads_application_settings_from_env(self):
        """Settings should load application settings from environment variables."""
        env_vars = {
            "API_HOST": "0.0.0.0",
            "API_PORT": "9000",
            "DEBUG": "true",
            "LOG_LEVEL": "DEBUG",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            from app.config import get_settings
            get_settings.cache_clear()

            settings = get_settings()

            assert settings.api_host == "0.0.0.0"
            assert settings.api_port == 9000
            assert settings.debug is True
            assert settings.log_level == "DEBUG"


class TestDatabaseUrl:
    """Tests for database_url computed property."""

    def test_database_url_constructed_correctly(self):
        """database_url property should construct proper PostgreSQL connection URL."""
        env_vars = {
            "POSTGRES_HOST": "db.example.com",
            "POSTGRES_PORT": "5432",
            "POSTGRES_USER": "myuser",
            "POSTGRES_PASSWORD": "mypass",
            "POSTGRES_DB": "mydb",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            from app.config import get_settings
            get_settings.cache_clear()

            settings = get_settings()

            expected = "postgresql+asyncpg://myuser:mypass@db.example.com:5432/mydb"
            assert settings.database_url == expected

    def test_database_url_uses_default_port(self):
        """database_url should use default port when not specified."""
        env_vars = {
            "POSTGRES_HOST": "localhost",
            "POSTGRES_USER": "user",
            "POSTGRES_PASSWORD": "pass",
            "POSTGRES_DB": "db",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            from app.config import get_settings
            get_settings.cache_clear()

            settings = get_settings()

            assert ":5432/" in settings.database_url


class TestDefaultValues:
    """Tests for default configuration values."""

    def test_onet_api_base_url_default(self):
        """onet_api_base_url should default to O*NET services URL."""
        from app.config import Settings

        # Create Settings directly to test defaults without environment interference
        # Remove the env var if it exists
        original = os.environ.pop("ONET_API_BASE_URL", None)
        try:
            settings = Settings()
            assert settings.onet_api_base_url == "https://services.onetcenter.org/ws/"
        finally:
            if original is not None:
                os.environ["ONET_API_BASE_URL"] = original

    def test_anthropic_model_default(self):
        """anthropic_model should default to claude-sonnet-4-20250514."""
        from app.config import Settings

        original = os.environ.pop("ANTHROPIC_MODEL", None)
        try:
            settings = Settings()
            assert settings.anthropic_model == "claude-sonnet-4-20250514"
        finally:
            if original is not None:
                os.environ["ANTHROPIC_MODEL"] = original

    def test_debug_defaults_to_false(self):
        """debug should default to False."""
        from app.config import Settings

        original = os.environ.pop("DEBUG", None)
        try:
            settings = Settings()
            assert settings.debug is False
        finally:
            if original is not None:
                os.environ["DEBUG"] = original

    def test_log_level_defaults_to_info(self):
        """log_level should default to INFO."""
        from app.config import Settings

        original = os.environ.pop("LOG_LEVEL", None)
        try:
            settings = Settings()
            assert settings.log_level == "INFO"
        finally:
            if original is not None:
                os.environ["LOG_LEVEL"] = original


class TestGetSettingsSingleton:
    """Tests for get_settings() singleton pattern."""

    def test_get_settings_returns_cached_singleton(self):
        """get_settings() should return the same cached instance."""
        from app.config import get_settings
        get_settings.cache_clear()

        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2

    def test_get_settings_uses_lru_cache(self):
        """get_settings should be decorated with lru_cache."""
        from app.config import get_settings

        # lru_cache decorated functions have cache_info method
        assert hasattr(get_settings, "cache_info")
        assert hasattr(get_settings, "cache_clear")
