"""Unit tests for O*NET repository."""
import pytest
from unittest.mock import AsyncMock, MagicMock


def test_onet_repository_exists():
    """Test OnetRepository is importable."""
    from app.repositories.onet_repository import OnetRepository
    assert OnetRepository is not None


@pytest.mark.asyncio
async def test_search_occupations():
    """Test search_occupations method signature."""
    from app.repositories.onet_repository import OnetRepository

    mock_session = AsyncMock()
    repo = OnetRepository(mock_session)

    # Should have search_occupations method
    assert hasattr(repo, "search_occupations")
    assert callable(repo.search_occupations)


@pytest.mark.asyncio
async def test_get_occupation_by_code():
    """Test get_by_code method signature."""
    from app.repositories.onet_repository import OnetRepository

    mock_session = AsyncMock()
    repo = OnetRepository(mock_session)

    assert hasattr(repo, "get_by_code")
    assert callable(repo.get_by_code)


@pytest.mark.asyncio
async def test_get_gwas():
    """Test get_gwas method signature."""
    from app.repositories.onet_repository import OnetRepository

    mock_session = AsyncMock()
    repo = OnetRepository(mock_session)

    assert hasattr(repo, "get_gwas")
    assert callable(repo.get_gwas)


@pytest.mark.asyncio
async def test_get_dwas_for_occupation():
    """Test get_dwas_for_occupation method signature."""
    from app.repositories.onet_repository import OnetRepository

    mock_session = AsyncMock()
    repo = OnetRepository(mock_session)

    assert hasattr(repo, "get_dwas_for_occupation")
    assert callable(repo.get_dwas_for_occupation)
