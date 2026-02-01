"""Unit tests for session repository."""
import pytest
from unittest.mock import AsyncMock
from uuid import uuid4


def test_session_repository_exists():
    """Test SessionRepository is importable."""
    from app.repositories.session_repository import SessionRepository
    assert SessionRepository is not None


@pytest.mark.asyncio
async def test_create_session():
    """Test create method signature."""
    from app.repositories.session_repository import SessionRepository

    mock_session = AsyncMock()
    repo = SessionRepository(mock_session)

    assert hasattr(repo, "create")
    assert callable(repo.create)


@pytest.mark.asyncio
async def test_get_by_id():
    """Test get_by_id method signature."""
    from app.repositories.session_repository import SessionRepository

    mock_session = AsyncMock()
    repo = SessionRepository(mock_session)

    assert hasattr(repo, "get_by_id")
    assert callable(repo.get_by_id)


@pytest.mark.asyncio
async def test_list_for_user():
    """Test list_for_user method signature."""
    from app.repositories.session_repository import SessionRepository

    mock_session = AsyncMock()
    repo = SessionRepository(mock_session)

    assert hasattr(repo, "list_for_user")
    assert callable(repo.list_for_user)


@pytest.mark.asyncio
async def test_update_step():
    """Test update_step method signature."""
    from app.repositories.session_repository import SessionRepository

    mock_session = AsyncMock()
    repo = SessionRepository(mock_session)

    assert hasattr(repo, "update_step")
    assert callable(repo.update_step)


@pytest.mark.asyncio
async def test_delete():
    """Test delete method signature."""
    from app.repositories.session_repository import SessionRepository

    mock_session = AsyncMock()
    repo = SessionRepository(mock_session)

    assert hasattr(repo, "delete")
    assert callable(repo.delete)
