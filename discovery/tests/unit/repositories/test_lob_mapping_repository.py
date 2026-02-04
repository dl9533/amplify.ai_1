"""Unit tests for LOB mapping repository."""
import pytest
from unittest.mock import AsyncMock


def test_lob_mapping_repository_exists():
    """Test LobMappingRepository is importable."""
    from app.repositories.lob_mapping_repository import LobMappingRepository
    assert LobMappingRepository is not None


@pytest.mark.asyncio
async def test_find_by_pattern():
    """Test find_by_pattern method signature."""
    from app.repositories.lob_mapping_repository import LobMappingRepository

    mock_session = AsyncMock()
    repo = LobMappingRepository(mock_session)

    assert hasattr(repo, "find_by_pattern")
    assert callable(repo.find_by_pattern)


@pytest.mark.asyncio
async def test_find_fuzzy():
    """Test find_fuzzy method signature."""
    from app.repositories.lob_mapping_repository import LobMappingRepository

    mock_session = AsyncMock()
    repo = LobMappingRepository(mock_session)

    assert hasattr(repo, "find_fuzzy")
    assert callable(repo.find_fuzzy)


@pytest.mark.asyncio
async def test_create():
    """Test create method signature."""
    from app.repositories.lob_mapping_repository import LobMappingRepository

    mock_session = AsyncMock()
    repo = LobMappingRepository(mock_session)

    assert hasattr(repo, "create")
    assert callable(repo.create)


@pytest.mark.asyncio
async def test_get_all():
    """Test get_all method signature."""
    from app.repositories.lob_mapping_repository import LobMappingRepository

    mock_session = AsyncMock()
    repo = LobMappingRepository(mock_session)

    assert hasattr(repo, "get_all")
    assert callable(repo.get_all)


@pytest.mark.asyncio
async def test_bulk_upsert():
    """Test bulk_upsert method signature."""
    from app.repositories.lob_mapping_repository import LobMappingRepository

    mock_session = AsyncMock()
    repo = LobMappingRepository(mock_session)

    assert hasattr(repo, "bulk_upsert")
    assert callable(repo.bulk_upsert)


@pytest.mark.asyncio
async def test_delete_by_pattern():
    """Test delete_by_pattern method signature."""
    from app.repositories.lob_mapping_repository import LobMappingRepository

    mock_session = AsyncMock()
    repo = LobMappingRepository(mock_session)

    assert hasattr(repo, "delete_by_pattern")
    assert callable(repo.delete_by_pattern)


def test_lob_mapping_repository_exported_from_init():
    """Test LobMappingRepository is exported from repositories __init__."""
    from app.repositories import LobMappingRepository
    assert LobMappingRepository is not None
