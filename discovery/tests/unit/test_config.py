"""Tests for configuration module with pydantic-settings."""
import pytest


class TestSettingsFromEnvironment:
    """Tests for loading settings from environment variables."""

    def test_settings_loads_database_config_from_env(self, monkeypatch):
        """Settings should load database configuration from environment variables."""
        monkeypatch.setenv("POSTGRES_HOST", "db.example.com")
        monkeypatch.setenv("POSTGRES_PORT", "5433")
        monkeypatch.setenv("POSTGRES_USER", "test_user")
        monkeypatch.setenv("POSTGRES_PASSWORD", "test_pass")
        monkeypatch.setenv("POSTGRES_DB", "test_db")

        from app.config import get_settings
        get_settings.cache_clear()

        settings = get_settings()

        assert settings.postgres_host == "db.example.com"
        assert settings.postgres_port == 5433
        assert settings.postgres_user == "test_user"
        assert settings.postgres_password.get_secret_value() == "test_pass"
        assert settings.postgres_db == "test_db"

    def test_settings_loads_redis_config_from_env(self, monkeypatch):
        """Settings should load Redis configuration from environment variables."""
        monkeypatch.setenv("REDIS_URL", "redis://redis.example.com:6380/1")

        from app.config import get_settings
        get_settings.cache_clear()

        settings = get_settings()

        assert settings.redis_url == "redis://redis.example.com:6380/1"

    def test_settings_loads_s3_config_from_env(self, monkeypatch):
        """Settings should load S3 configuration from environment variables."""
        monkeypatch.setenv("S3_ENDPOINT_URL", "http://minio:9000")
        monkeypatch.setenv("S3_BUCKET", "test-bucket")
        monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test_access_key")
        monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test_secret_key")
        monkeypatch.setenv("AWS_REGION", "eu-west-1")

        from app.config import get_settings
        get_settings.cache_clear()

        settings = get_settings()

        assert settings.s3_endpoint_url == "http://minio:9000"
        assert settings.s3_bucket == "test-bucket"
        assert settings.aws_access_key_id == "test_access_key"
        assert settings.aws_secret_access_key.get_secret_value() == "test_secret_key"
        assert settings.aws_region == "eu-west-1"

    def test_settings_loads_onet_config_from_env(self, monkeypatch):
        """Settings should load O*NET API configuration from environment variables."""
        monkeypatch.setenv("ONET_API_KEY", "onet_test_key_12345")
        monkeypatch.setenv("ONET_API_BASE_URL", "https://custom.onet.org/api/")

        from app.config import get_settings
        get_settings.cache_clear()

        settings = get_settings()

        assert settings.onet_api_key.get_secret_value() == "onet_test_key_12345"
        assert settings.onet_api_base_url == "https://custom.onet.org/api/"

    def test_settings_loads_anthropic_config_from_env(self, monkeypatch):
        """Settings should load Anthropic configuration from environment variables."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key")
        monkeypatch.setenv("ANTHROPIC_MODEL", "claude-opus-4-20250514")

        from app.config import get_settings
        get_settings.cache_clear()

        settings = get_settings()

        assert settings.anthropic_api_key.get_secret_value() == "sk-ant-test-key"
        assert settings.anthropic_model == "claude-opus-4-20250514"

    def test_settings_loads_application_settings_from_env(self, monkeypatch):
        """Settings should load application settings from environment variables."""
        monkeypatch.setenv("API_HOST", "0.0.0.0")
        monkeypatch.setenv("API_PORT", "9000")
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")

        from app.config import get_settings
        get_settings.cache_clear()

        settings = get_settings()

        assert settings.api_host == "0.0.0.0"
        assert settings.api_port == 9000
        assert settings.debug is True
        assert settings.log_level == "DEBUG"


class TestDatabaseUrl:
    """Tests for database_url computed property."""

    def test_database_url_constructed_correctly(self, monkeypatch):
        """database_url property should construct proper PostgreSQL connection URL."""
        monkeypatch.setenv("POSTGRES_HOST", "db.example.com")
        monkeypatch.setenv("POSTGRES_PORT", "5432")
        monkeypatch.setenv("POSTGRES_USER", "myuser")
        monkeypatch.setenv("POSTGRES_PASSWORD", "mypass")
        monkeypatch.setenv("POSTGRES_DB", "mydb")

        from app.config import get_settings
        get_settings.cache_clear()

        settings = get_settings()

        expected = "postgresql+asyncpg://myuser:mypass@db.example.com:5432/mydb"
        assert settings.database_url == expected

    def test_database_url_uses_default_port(self, monkeypatch):
        """database_url should use default port when not specified."""
        monkeypatch.setenv("POSTGRES_HOST", "localhost")
        monkeypatch.setenv("POSTGRES_USER", "user")
        monkeypatch.setenv("POSTGRES_PASSWORD", "pass")
        monkeypatch.setenv("POSTGRES_DB", "db")

        from app.config import get_settings
        get_settings.cache_clear()

        settings = get_settings()

        assert ":5432/" in settings.database_url

    def test_database_url_encodes_special_characters(self, monkeypatch):
        """database_url should URL-encode special characters in password."""
        monkeypatch.setenv("POSTGRES_HOST", "localhost")
        monkeypatch.setenv("POSTGRES_USER", "user")
        monkeypatch.setenv("POSTGRES_PASSWORD", "p@ss:word/with#special")
        monkeypatch.setenv("POSTGRES_DB", "db")

        from app.config import get_settings
        get_settings.cache_clear()

        settings = get_settings()

        # Password should be URL-encoded
        assert "p%40ss%3Aword%2Fwith%23special" in settings.database_url
        # Raw password should not appear
        assert "p@ss:word/with#special" not in settings.database_url


class TestDefaultValues:
    """Tests for default configuration values."""

    def test_onet_api_base_url_default(self, monkeypatch):
        """onet_api_base_url should default to O*NET services URL."""
        monkeypatch.delenv("ONET_API_BASE_URL", raising=False)

        from app.config import Settings

        settings = Settings()
        assert settings.onet_api_base_url == "https://services.onetcenter.org/ws/"

    def test_anthropic_model_default(self, monkeypatch):
        """anthropic_model should default to claude-sonnet-4-20250514."""
        monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)

        from app.config import Settings

        settings = Settings()
        assert settings.anthropic_model == "claude-sonnet-4-20250514"

    def test_debug_defaults_to_false(self, monkeypatch):
        """debug should default to False."""
        monkeypatch.delenv("DEBUG", raising=False)

        from app.config import Settings

        settings = Settings()
        assert settings.debug is False

    def test_log_level_defaults_to_info(self, monkeypatch):
        """log_level should default to INFO."""
        monkeypatch.delenv("LOG_LEVEL", raising=False)

        from app.config import Settings

        settings = Settings()
        assert settings.log_level == "INFO"


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


class TestSecretFieldProtection:
    """Tests for sensitive field protection in serialization."""

    def test_postgres_password_hidden_in_repr(self, monkeypatch):
        """postgres_password should be hidden in repr output."""
        monkeypatch.setenv("POSTGRES_PASSWORD", "super_secret_password")

        from app.config import get_settings
        get_settings.cache_clear()

        settings = get_settings()
        repr_output = repr(settings)

        assert "super_secret_password" not in repr_output
        assert "SecretStr" in repr_output or "**********" in repr_output

    def test_aws_secret_access_key_hidden_in_repr(self, monkeypatch):
        """aws_secret_access_key should be hidden in repr output."""
        monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "aws_super_secret")

        from app.config import get_settings
        get_settings.cache_clear()

        settings = get_settings()
        repr_output = repr(settings)

        assert "aws_super_secret" not in repr_output

    def test_onet_api_key_hidden_in_repr(self, monkeypatch):
        """onet_api_key should be hidden in repr output."""
        monkeypatch.setenv("ONET_API_KEY", "onet_secret_key")

        from app.config import get_settings
        get_settings.cache_clear()

        settings = get_settings()
        repr_output = repr(settings)

        assert "onet_secret_key" not in repr_output

    def test_anthropic_api_key_hidden_in_repr(self, monkeypatch):
        """anthropic_api_key should be hidden in repr output."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-secret")

        from app.config import get_settings
        get_settings.cache_clear()

        settings = get_settings()
        repr_output = repr(settings)

        assert "sk-ant-secret" not in repr_output

    def test_database_url_hidden_in_repr(self, monkeypatch):
        """database_url should be hidden in repr output (contains password)."""
        monkeypatch.setenv("POSTGRES_PASSWORD", "db_password_secret")

        from app.config import get_settings
        get_settings.cache_clear()

        settings = get_settings()
        repr_output = repr(settings)

        # database_url should not appear in repr
        assert "database_url" not in repr_output
        assert "db_password_secret" not in repr_output

    def test_model_dump_excludes_secret_values(self, monkeypatch):
        """model_dump() should not expose secret values as plain strings."""
        monkeypatch.setenv("POSTGRES_PASSWORD", "secret_pg_pass")
        monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret_aws_key")
        monkeypatch.setenv("ONET_API_KEY", "secret_onet_key")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "secret_anthropic_key")

        from app.config import get_settings
        get_settings.cache_clear()

        settings = get_settings()
        dumped = settings.model_dump()

        # Secret values should be SecretStr objects, not exposed strings
        assert dumped["postgres_password"] != "secret_pg_pass"
        assert dumped["aws_secret_access_key"] != "secret_aws_key"
        assert dumped["onet_api_key"] != "secret_onet_key"
        assert dumped["anthropic_api_key"] != "secret_anthropic_key"

    def test_str_output_hides_secrets(self, monkeypatch):
        """str() output should hide sensitive fields."""
        monkeypatch.setenv("POSTGRES_PASSWORD", "str_secret_pass")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "str_secret_key")

        from app.config import get_settings
        get_settings.cache_clear()

        settings = get_settings()
        str_output = str(settings)

        assert "str_secret_pass" not in str_output
        assert "str_secret_key" not in str_output
