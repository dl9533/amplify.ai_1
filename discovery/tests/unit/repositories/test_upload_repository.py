"""Unit tests for upload repository."""
import pytest
from unittest.mock import AsyncMock


def test_upload_repository_exists():
    """Test UploadRepository is importable."""
    from app.repositories.upload_repository import UploadRepository
    assert UploadRepository is not None


@pytest.mark.asyncio
async def test_create_upload():
    """Test create method exists."""
    from app.repositories.upload_repository import UploadRepository

    mock_session = AsyncMock()
    repo = UploadRepository(mock_session)

    assert hasattr(repo, "create")


@pytest.mark.asyncio
async def test_get_for_session():
    """Test get_for_session method exists."""
    from app.repositories.upload_repository import UploadRepository

    mock_session = AsyncMock()
    repo = UploadRepository(mock_session)

    assert hasattr(repo, "get_for_session")


@pytest.mark.asyncio
async def test_get_by_id():
    """Test get_by_id method exists."""
    from app.repositories.upload_repository import UploadRepository

    mock_session = AsyncMock()
    repo = UploadRepository(mock_session)

    assert hasattr(repo, "get_by_id")


@pytest.mark.asyncio
async def test_update_mappings():
    """Test update_mappings method exists."""
    from app.repositories.upload_repository import UploadRepository

    mock_session = AsyncMock()
    repo = UploadRepository(mock_session)

    assert hasattr(repo, "update_mappings")
