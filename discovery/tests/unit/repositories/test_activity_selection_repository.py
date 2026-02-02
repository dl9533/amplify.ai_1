# discovery/tests/unit/repositories/test_activity_selection_repository.py
"""Unit tests for activity selection repository."""
import pytest
from unittest.mock import AsyncMock


def test_activity_selection_repository_exists():
    """Test ActivitySelectionRepository is importable."""
    from app.repositories.activity_selection_repository import ActivitySelectionRepository
    assert ActivitySelectionRepository is not None


@pytest.mark.asyncio
async def test_bulk_create():
    """Test bulk_create method exists."""
    from app.repositories.activity_selection_repository import ActivitySelectionRepository

    mock_session = AsyncMock()
    repo = ActivitySelectionRepository(mock_session)

    assert hasattr(repo, "bulk_create")


@pytest.mark.asyncio
async def test_get_for_role_mapping():
    """Test get_for_role_mapping method exists."""
    from app.repositories.activity_selection_repository import ActivitySelectionRepository

    mock_session = AsyncMock()
    repo = ActivitySelectionRepository(mock_session)

    assert hasattr(repo, "get_for_role_mapping")


@pytest.mark.asyncio
async def test_update_selection():
    """Test update_selection method exists."""
    from app.repositories.activity_selection_repository import ActivitySelectionRepository

    mock_session = AsyncMock()
    repo = ActivitySelectionRepository(mock_session)

    assert hasattr(repo, "update_selection")


@pytest.mark.asyncio
async def test_get_for_session():
    """Test get_for_session method exists."""
    from app.repositories.activity_selection_repository import ActivitySelectionRepository

    mock_session = AsyncMock()
    repo = ActivitySelectionRepository(mock_session)

    assert hasattr(repo, "get_for_session")
