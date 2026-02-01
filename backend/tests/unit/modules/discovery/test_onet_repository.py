# backend/tests/unit/modules/discovery/test_onet_repository.py
"""Unit tests for OnetOccupationRepository."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.modules.discovery.repositories.onet_repository import OnetOccupationRepository
from app.modules.discovery.models.onet import OnetOccupation


@pytest.mark.asyncio
async def test_create_occupation(mock_db_session):
    """Should create an O*NET occupation record."""
    repo = OnetOccupationRepository(mock_db_session)

    # Create the occupation
    occupation = await repo.create(
        code="15-1252.00",
        title="Software Developers",
        description="Develop applications"
    )

    assert occupation.code == "15-1252.00"
    assert occupation.title == "Software Developers"
    assert occupation.description == "Develop applications"
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_occupation_without_description(mock_db_session):
    """Should create occupation without optional description."""
    repo = OnetOccupationRepository(mock_db_session)

    occupation = await repo.create(
        code="15-1252.00",
        title="Software Developers"
    )

    assert occupation.code == "15-1252.00"
    assert occupation.title == "Software Developers"
    assert occupation.description is None


@pytest.mark.asyncio
async def test_get_by_code(mock_db_session):
    """Should retrieve occupation by code."""
    repo = OnetOccupationRepository(mock_db_session)

    # Create a mock occupation
    mock_occupation = OnetOccupation(
        code="15-1252.00",
        title="Software Developers",
        description="Develop applications"
    )

    # Configure mock to return occupation
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = mock_occupation

    result = await repo.get_by_code("15-1252.00")
    assert result is not None
    assert result.title == "Software Developers"
    assert result.code == "15-1252.00"


@pytest.mark.asyncio
async def test_get_by_code_not_found(mock_db_session):
    """Should return None when occupation not found."""
    repo = OnetOccupationRepository(mock_db_session)

    # Configure mock to return None
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = None

    result = await repo.get_by_code("99-9999.99")
    assert result is None


@pytest.mark.asyncio
async def test_search_by_title(mock_db_session):
    """Should search occupations by title keyword."""
    repo = OnetOccupationRepository(mock_db_session)

    # Create mock occupations
    mock_occupation = OnetOccupation(
        code="15-1252.00",
        title="Software Developers",
        description="Develop applications"
    )

    # Configure mock to return matching results
    mock_result = mock_db_session.execute.return_value
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [mock_occupation]
    mock_result.scalars.return_value = mock_scalars

    results = await repo.search("software")
    assert len(results) == 1
    assert results[0].code == "15-1252.00"


@pytest.mark.asyncio
async def test_search_returns_empty_list(mock_db_session):
    """Should return empty list when no matches found."""
    repo = OnetOccupationRepository(mock_db_session)

    # Configure mock to return empty results
    mock_result = mock_db_session.execute.return_value
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars

    results = await repo.search("nonexistent")
    assert len(results) == 0


@pytest.mark.asyncio
async def test_upsert_creates_new_occupation(mock_db_session):
    """Should insert new occupation when code doesn't exist."""
    repo = OnetOccupationRepository(mock_db_session)

    # Configure mock to return None (no existing record)
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = None

    result = await repo.upsert(code="15-1252.00", title="Software Developers")

    assert result.code == "15-1252.00"
    assert result.title == "Software Developers"
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called()


@pytest.mark.asyncio
async def test_upsert_updates_existing_occupation(mock_db_session):
    """Should update occupation when code already exists."""
    repo = OnetOccupationRepository(mock_db_session)

    # Create mock existing occupation
    existing = OnetOccupation(
        code="15-1252.00",
        title="Software Developers"
    )

    # Configure mock to return existing occupation
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = existing

    result = await repo.upsert(
        code="15-1252.00",
        title="Software Developers, Applications"
    )

    assert result.title == "Software Developers, Applications"
    # Should not call add since we're updating
    mock_db_session.add.assert_not_called()
    mock_db_session.commit.assert_called()


@pytest.mark.asyncio
async def test_upsert_updates_description(mock_db_session):
    """Should update description on upsert."""
    repo = OnetOccupationRepository(mock_db_session)

    # Create mock existing occupation without description
    existing = OnetOccupation(
        code="15-1252.00",
        title="Software Developers",
        description=None
    )

    # Configure mock to return existing occupation
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = existing

    result = await repo.upsert(
        code="15-1252.00",
        title="Software Developers",
        description="New description"
    )

    assert result.description == "New description"


@pytest.mark.asyncio
async def test_list_all(mock_db_session):
    """Should list all occupations."""
    repo = OnetOccupationRepository(mock_db_session)

    # Create mock occupations
    occupation1 = OnetOccupation(code="15-1252.00", title="Software Developers")
    occupation2 = OnetOccupation(code="43-4051.00", title="Customer Service Representatives")

    # Configure mock to return all occupations
    mock_result = mock_db_session.execute.return_value
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [occupation1, occupation2]
    mock_result.scalars.return_value = mock_scalars

    results = await repo.list_all()
    assert len(results) == 2


@pytest.mark.asyncio
async def test_delete_by_code(mock_db_session):
    """Should delete occupation by code."""
    repo = OnetOccupationRepository(mock_db_session)

    # Create mock existing occupation
    existing = OnetOccupation(
        code="15-1252.00",
        title="Software Developers"
    )

    # Configure mock to return existing occupation
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = existing

    result = await repo.delete_by_code("15-1252.00")
    assert result is True
    mock_db_session.commit.assert_called()


@pytest.mark.asyncio
async def test_delete_by_code_not_found(mock_db_session):
    """Should return False when trying to delete non-existent occupation."""
    repo = OnetOccupationRepository(mock_db_session)

    # Configure mock to return None
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = None

    result = await repo.delete_by_code("99-9999.99")
    assert result is False
