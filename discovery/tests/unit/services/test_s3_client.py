"""Unit tests for S3 client."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def test_s3_client_exists():
    """Test S3Client is importable."""
    from app.services.s3_client import S3Client
    assert S3Client is not None


@pytest.mark.asyncio
async def test_upload_file():
    """Test upload_file method."""
    from app.services.s3_client import S3Client

    client = S3Client(
        endpoint_url="http://localhost:4566",
        bucket="test-bucket",
        access_key="test",
        secret_key="test",
        region="us-east-1",
    )

    assert hasattr(client, "upload_file")
    assert callable(client.upload_file)


@pytest.mark.asyncio
async def test_download_file():
    """Test download_file method."""
    from app.services.s3_client import S3Client

    client = S3Client(
        endpoint_url="http://localhost:4566",
        bucket="test-bucket",
        access_key="test",
        secret_key="test",
        region="us-east-1",
    )

    assert hasattr(client, "download_file")
    assert callable(client.download_file)


@pytest.mark.asyncio
async def test_delete_file():
    """Test delete_file method."""
    from app.services.s3_client import S3Client

    client = S3Client(
        endpoint_url="http://localhost:4566",
        bucket="test-bucket",
        access_key="test",
        secret_key="test",
        region="us-east-1",
    )

    assert hasattr(client, "delete_file")
    assert callable(client.delete_file)


def test_get_client_config():
    """Test client config generation."""
    from app.services.s3_client import S3Client

    client = S3Client(
        endpoint_url="http://localhost:4566",
        bucket="test-bucket",
        access_key="test_key",
        secret_key="test_secret",
        region="us-east-1",
    )

    config = client._get_client_config()
    assert config["service_name"] == "s3"
    assert config["region_name"] == "us-east-1"
    assert config["endpoint_url"] == "http://localhost:4566"
