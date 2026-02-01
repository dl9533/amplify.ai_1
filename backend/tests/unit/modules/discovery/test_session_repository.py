# backend/tests/unit/modules/discovery/test_session_repository.py
"""Unit tests for DiscoverySessionRepository."""

import pytest
from uuid import uuid4
from unittest.mock import MagicMock

from app.modules.discovery.repositories.session_repository import (
    DiscoverySessionRepository,
)
from app.modules.discovery.models.session import DiscoverySession
from app.modules.discovery.enums import SessionStatus


@pytest.mark.asyncio
async def test_create_session(mock_db_session):
    """Should create a discovery session."""
    repo = DiscoverySessionRepository(mock_db_session)
    user_id = uuid4()
    org_id = uuid4()

    session = await repo.create(user_id=user_id, organization_id=org_id)

    assert session.user_id == user_id
    assert session.organization_id == org_id
    assert session.status == SessionStatus.DRAFT
    assert session.current_step == 1
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_get_session_by_id(mock_db_session):
    """Should retrieve session by ID."""
    repo = DiscoverySessionRepository(mock_db_session)
    session_id = uuid4()

    # Create a mock session
    mock_session = DiscoverySession(
        id=session_id,
        user_id=uuid4(),
        organization_id=uuid4(),
        status=SessionStatus.DRAFT,
        current_step=1,
    )

    # Configure mock to return session
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = mock_session

    retrieved = await repo.get_by_id(session_id)

    assert retrieved is not None
    assert retrieved.id == session_id


@pytest.mark.asyncio
async def test_get_session_by_id_not_found(mock_db_session):
    """Should return None when session not found."""
    repo = DiscoverySessionRepository(mock_db_session)

    # Configure mock to return None
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = None

    result = await repo.get_by_id(uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_update_session_step(mock_db_session):
    """Should update current step."""
    repo = DiscoverySessionRepository(mock_db_session)
    session_id = uuid4()

    # Create mock session
    mock_session = DiscoverySession(
        id=session_id,
        user_id=uuid4(),
        organization_id=uuid4(),
        status=SessionStatus.DRAFT,
        current_step=1,
    )

    # Configure mock to return session for get_by_id
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = mock_session

    updated = await repo.update_step(session_id, step=2)

    assert updated.current_step == 2
    mock_db_session.commit.assert_called()


@pytest.mark.asyncio
async def test_update_session_step_not_found(mock_db_session):
    """Should return None when session to update not found."""
    repo = DiscoverySessionRepository(mock_db_session)

    # Configure mock to return None
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = None

    result = await repo.update_step(uuid4(), step=2)
    assert result is None


@pytest.mark.asyncio
async def test_update_session_status(mock_db_session):
    """Should update session status."""
    repo = DiscoverySessionRepository(mock_db_session)
    session_id = uuid4()

    # Create mock session
    mock_session = DiscoverySession(
        id=session_id,
        user_id=uuid4(),
        organization_id=uuid4(),
        status=SessionStatus.DRAFT,
        current_step=1,
    )

    # Configure mock to return session
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = mock_session

    updated = await repo.update_status(session_id, SessionStatus.IN_PROGRESS)

    assert updated.status == SessionStatus.IN_PROGRESS
    mock_db_session.commit.assert_called()


@pytest.mark.asyncio
async def test_update_session_status_not_found(mock_db_session):
    """Should return None when session to update not found."""
    repo = DiscoverySessionRepository(mock_db_session)

    # Configure mock to return None
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = None

    result = await repo.update_status(uuid4(), SessionStatus.IN_PROGRESS)
    assert result is None


@pytest.mark.asyncio
async def test_list_sessions_for_user(mock_db_session):
    """Should list sessions for a user."""
    repo = DiscoverySessionRepository(mock_db_session)
    user_id = uuid4()
    org_id = uuid4()

    # Create mock sessions
    session1 = DiscoverySession(
        id=uuid4(),
        user_id=user_id,
        organization_id=org_id,
        status=SessionStatus.DRAFT,
        current_step=1,
    )
    session2 = DiscoverySession(
        id=uuid4(),
        user_id=user_id,
        organization_id=org_id,
        status=SessionStatus.IN_PROGRESS,
        current_step=2,
    )

    # Configure mock to return sessions
    mock_result = mock_db_session.execute.return_value
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [session1, session2]
    mock_result.scalars.return_value = mock_scalars

    sessions = await repo.list_for_user(user_id)

    assert len(sessions) == 2


@pytest.mark.asyncio
async def test_list_sessions_for_user_empty(mock_db_session):
    """Should return empty list when user has no sessions."""
    repo = DiscoverySessionRepository(mock_db_session)

    # Configure mock to return empty list
    mock_result = mock_db_session.execute.return_value
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars

    sessions = await repo.list_for_user(uuid4())

    assert len(sessions) == 0


@pytest.mark.asyncio
async def test_delete_session(mock_db_session):
    """Should delete a session by ID."""
    repo = DiscoverySessionRepository(mock_db_session)
    session_id = uuid4()

    # Create mock session
    mock_session = DiscoverySession(
        id=session_id,
        user_id=uuid4(),
        organization_id=uuid4(),
        status=SessionStatus.DRAFT,
        current_step=1,
    )

    # Configure mock to return session
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = mock_session

    result = await repo.delete(session_id)

    assert result is True
    mock_db_session.delete.assert_called_once_with(mock_session)
    mock_db_session.commit.assert_called()


@pytest.mark.asyncio
async def test_delete_session_not_found(mock_db_session):
    """Should return False when session to delete not found."""
    repo = DiscoverySessionRepository(mock_db_session)

    # Configure mock to return None
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = None

    result = await repo.delete(uuid4())

    assert result is False
    mock_db_session.delete.assert_not_called()
