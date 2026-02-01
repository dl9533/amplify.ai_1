import pytest
from pathlib import Path


def test_pyproject_toml_exists():
    """pyproject.toml should exist with project metadata."""
    path = Path(__file__).parent.parent / "pyproject.toml"
    assert path.exists()

    content = path.read_text()
    assert "[project]" in content
    assert 'name = "discovery"' in content or "name = 'discovery'" in content
    assert "fastapi" in content.lower()


def test_requirements_txt_exists():
    """requirements.txt should exist with dependencies."""
    path = Path(__file__).parent.parent / "requirements.txt"
    assert path.exists()

    content = path.read_text()
    assert "fastapi" in content.lower()
    assert "sqlalchemy" in content.lower()
    assert "httpx" in content.lower()  # For O*NET API calls
    assert "boto3" in content.lower()  # For S3


def test_discovery_package_exists():
    """discovery package should be importable."""
    import discovery
    assert discovery is not None


def test_config_loads():
    """Config should load from environment."""
    from discovery.config import Settings

    # Should have discovery-specific settings
    fields = Settings.model_fields.keys()
    assert "postgres_host" in fields
    assert "redis_url" in fields
    assert "s3_bucket" in fields
    assert "onet_api_username" in fields
