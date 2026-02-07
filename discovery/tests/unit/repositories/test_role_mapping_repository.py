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


@pytest.mark.asyncio
async def test_get_by_id_exists():
    """Test get_by_id method exists."""
    from app.repositories.role_mapping_repository import RoleMappingRepository

    mock_session = AsyncMock()
    repo = RoleMappingRepository(mock_session)

    assert hasattr(repo, "get_by_id")


@pytest.mark.asyncio
async def test_get_by_id_accepts_session_id_parameter():
    """Test get_by_id accepts optional session_id parameter for authorization."""
    from uuid import uuid4
    from app.repositories.role_mapping_repository import RoleMappingRepository
    import inspect

    mock_session = AsyncMock()
    repo = RoleMappingRepository(mock_session)

    # Verify the method signature includes session_id parameter
    sig = inspect.signature(repo.get_by_id)
    params = list(sig.parameters.keys())

    assert "mapping_id" in params
    assert "session_id" in params


@pytest.mark.asyncio
async def test_delete_for_session():
    """Test delete_for_session method exists."""
    from app.repositories.role_mapping_repository import RoleMappingRepository

    mock_session = AsyncMock()
    repo = RoleMappingRepository(mock_session)

    assert hasattr(repo, "delete_for_session")
