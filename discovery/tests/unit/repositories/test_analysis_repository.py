"""Unit tests for analysis repository."""
import pytest
from unittest.mock import AsyncMock


def test_analysis_repository_exists():
    """Test AnalysisRepository is importable."""
    from app.repositories.analysis_repository import AnalysisRepository
    assert AnalysisRepository is not None


@pytest.mark.asyncio
async def test_save_results():
    """Test save_results method exists."""
    from app.repositories.analysis_repository import AnalysisRepository

    mock_session = AsyncMock()
    repo = AnalysisRepository(mock_session)

    assert hasattr(repo, "save_results")


@pytest.mark.asyncio
async def test_get_for_session():
    """Test get_for_session method exists."""
    from app.repositories.analysis_repository import AnalysisRepository

    mock_session = AsyncMock()
    repo = AnalysisRepository(mock_session)

    assert hasattr(repo, "get_for_session")


@pytest.mark.asyncio
async def test_get_by_role_mapping():
    """Test get_by_role_mapping method exists."""
    from app.repositories.analysis_repository import AnalysisRepository

    mock_session = AsyncMock()
    repo = AnalysisRepository(mock_session)

    assert hasattr(repo, "get_by_role_mapping")
