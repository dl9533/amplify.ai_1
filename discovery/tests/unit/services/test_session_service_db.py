"""Unit tests for database-backed session service."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4


@pytest.mark.asyncio
async def test_session_service_create():
    """Test session creation with repository."""
    from app.services.session_service import SessionService

    mock_repo = AsyncMock()
    mock_session = MagicMock()
    mock_session.id = uuid4()
    mock_session.current_step = 1
    mock_session.status = MagicMock()
    mock_session.status.value = "draft"
    mock_session.created_at = MagicMock()
    mock_session.created_at.isoformat.return_value = "2026-02-01T00:00:00"
    mock_repo.create.return_value = mock_session

    service = SessionService(repository=mock_repo, user_id=uuid4())
    result = await service.create(organization_id=uuid4())

    assert result is not None
    mock_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_session_service_get_by_id():
    """Test session retrieval with repository."""
    from app.services.session_service import SessionService

    mock_repo = AsyncMock()
    mock_session = MagicMock()
    mock_session.id = uuid4()
    mock_session.status = MagicMock()
    mock_session.status.value = "draft"
    mock_session.current_step = 1
    mock_session.created_at = MagicMock()
    mock_session.created_at.isoformat.return_value = "2026-02-01T00:00:00"
    mock_session.updated_at = MagicMock()
    mock_session.updated_at.isoformat.return_value = "2026-02-01T00:00:00"
    mock_repo.get_by_id.return_value = mock_session

    service = SessionService(repository=mock_repo)
    session_id = uuid4()
    result = await service.get_by_id(session_id)

    mock_repo.get_by_id.assert_called_once_with(session_id)


@pytest.mark.asyncio
async def test_session_service_no_longer_raises_not_implemented():
    """Test service no longer raises NotImplementedError."""
    from app.services.session_service import SessionService

    mock_repo = AsyncMock()
    mock_session = MagicMock()
    mock_session.id = uuid4()
    mock_session.current_step = 1
    mock_session.status = MagicMock()
    mock_session.status.value = "draft"
    mock_session.created_at = MagicMock()
    mock_session.created_at.isoformat.return_value = "2026-02-01T00:00:00"
    mock_repo.create.return_value = mock_session

    service = SessionService(repository=mock_repo, user_id=uuid4())

    # Should not raise NotImplementedError
    result = await service.create(organization_id=uuid4())
    assert result is not None


@pytest.mark.asyncio
async def test_session_service_list_for_user():
    """Test list sessions for user."""
    from app.services.session_service import SessionService

    mock_repo = AsyncMock()
    mock_session = MagicMock()
    mock_session.id = uuid4()
    mock_session.status = MagicMock()
    mock_session.status.value = "draft"
    mock_session.current_step = 1
    mock_session.updated_at = MagicMock()
    mock_session.updated_at.isoformat.return_value = "2026-02-01T00:00:00"
    mock_repo.list_for_user.return_value = ([mock_session], 1)

    user_id = uuid4()
    service = SessionService(repository=mock_repo, user_id=user_id)
    result = await service.list_for_user(page=1, per_page=10)

    assert "items" in result
    assert "total" in result
    assert result["total"] == 1


@pytest.mark.asyncio
async def test_session_service_update_step():
    """Test update session step."""
    from app.services.session_service import SessionService

    mock_repo = AsyncMock()
    mock_session = MagicMock()
    mock_session.id = uuid4()
    mock_session.status = MagicMock()
    mock_session.status.value = "in_progress"
    mock_session.current_step = 2
    mock_repo.update_step.return_value = mock_session

    service = SessionService(repository=mock_repo)
    result = await service.update_step(session_id=uuid4(), step=2)

    assert result is not None
    assert result["current_step"] == 2


@pytest.mark.asyncio
async def test_session_service_delete():
    """Test delete session."""
    from app.services.session_service import SessionService

    mock_repo = AsyncMock()
    mock_repo.delete.return_value = True

    service = SessionService(repository=mock_repo)
    result = await service.delete(session_id=uuid4())

    assert result is True
