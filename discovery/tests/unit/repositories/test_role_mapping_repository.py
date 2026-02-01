"""Unit tests for role mapping repository."""
import pytest
from unittest.mock import AsyncMock


def test_role_mapping_repository_exists():
    """Test RoleMappingRepository is importable."""
    from app.repositories.role_mapping_repository import RoleMappingRepository
    assert RoleMappingRepository is not None


@pytest.mark.asyncio
async def test_create_mapping():
    """Test create method exists."""
    from app.repositories.role_mapping_repository import RoleMappingRepository

    mock_session = AsyncMock()
    repo = RoleMappingRepository(mock_session)

    assert hasattr(repo, "create")


@pytest.mark.asyncio
async def test_bulk_create():
    """Test bulk_create method exists."""
    from app.repositories.role_mapping_repository import RoleMappingRepository

    mock_session = AsyncMock()
    repo = RoleMappingRepository(mock_session)

    assert hasattr(repo, "bulk_create")


@pytest.mark.asyncio
async def test_confirm_mapping():
    """Test confirm method exists."""
    from app.repositories.role_mapping_repository import RoleMappingRepository

    mock_session = AsyncMock()
    repo = RoleMappingRepository(mock_session)

    assert hasattr(repo, "confirm")


@pytest.mark.asyncio
async def test_get_for_session():
    """Test get_for_session method exists."""
    from app.repositories.role_mapping_repository import RoleMappingRepository

    mock_session = AsyncMock()
    repo = RoleMappingRepository(mock_session)

    assert hasattr(repo, "get_for_session")
