"""Pytest fixtures for discovery module unit tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_db_session():
    """Create a mock async database session.

    Returns a MagicMock configured with AsyncMock for async operations
    (execute, commit, refresh, delete) and a regular MagicMock for sync
    operations (add).

    The mock.execute.return_value is a MagicMock that supports both:
    - scalar_one_or_none() for single result queries
    - scalars().all() for multiple result queries

    Tests should configure this by setting:
    - mock_db_session.execute.return_value.scalar_one_or_none.return_value = value
    - mock_db_session.execute.return_value.scalars.return_value.all.return_value = [list]
    """
    session = MagicMock()
    # Create a result mock that will be returned when execute() is awaited
    result_mock = MagicMock()
    # AsyncMock for execute that returns our result mock
    session.execute = AsyncMock(return_value=result_mock)
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    session.delete = AsyncMock()
    return session
