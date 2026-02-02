# discovery/tests/unit/services/test_activity_service_impl.py
"""Unit tests for implemented activity service."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4


@pytest.mark.asyncio
async def test_load_activities_for_mapping():
    """Test loading DWAs for a role mapping."""
    from app.services.activity_service import ActivityService

    mock_selection_repo = AsyncMock()
    mock_onet_repo = AsyncMock()

    # Mock DWAs from O*NET
    mock_dwa = MagicMock()
    mock_dwa.id = "4.A.1.a.1"
    mock_dwa.name = "Getting Information"
    mock_dwa.ai_exposure_override = None
    mock_dwa.iwa = MagicMock()
    mock_dwa.iwa.gwa = MagicMock()
    mock_dwa.iwa.gwa.ai_exposure_score = 0.75
    mock_onet_repo.get_dwas_for_occupation.return_value = [mock_dwa]

    # Mock bulk_create return
    mock_selection = MagicMock()
    mock_selection.id = uuid4()
    mock_selection.dwa_id = "4.A.1.a.1"
    mock_selection.selected = True
    mock_selection.user_modified = False
    mock_selection_repo.bulk_create.return_value = [mock_selection]

    service = ActivityService(
        selection_repository=mock_selection_repo,
        onet_repository=mock_onet_repo,
    )

    session_id = uuid4()
    mapping_id = uuid4()
    result = await service.load_activities_for_mapping(
        session_id=session_id,
        role_mapping_id=mapping_id,
        onet_code="15-1252.00",
    )

    mock_onet_repo.get_dwas_for_occupation.assert_called_once_with("15-1252.00")
    assert len(result) == 1


@pytest.mark.asyncio
async def test_get_selections():
    """Test getting activity selections."""
    from app.services.activity_service import ActivityService

    mock_repo = AsyncMock()
    mock_selection = MagicMock()
    mock_selection.id = uuid4()
    mock_selection.dwa_id = "4.A.1.a.1"
    mock_selection.selected = True
    mock_selection.user_modified = False
    mock_repo.get_for_role_mapping.return_value = [mock_selection]

    service = ActivityService(selection_repository=mock_repo)
    result = await service.get_selections(uuid4())

    assert len(result) == 1
    mock_repo.get_for_role_mapping.assert_called_once()


@pytest.mark.asyncio
async def test_get_session_selections():
    """Test getting all selections for a session."""
    from app.services.activity_service import ActivityService

    mock_repo = AsyncMock()
    mock_selection = MagicMock()
    mock_selection.id = uuid4()
    mock_selection.role_mapping_id = uuid4()
    mock_selection.dwa_id = "4.A.1.a.1"
    mock_selection.selected = True
    mock_selection.user_modified = False
    mock_repo.get_for_session.return_value = [mock_selection]

    service = ActivityService(selection_repository=mock_repo)
    result = await service.get_session_selections(uuid4())

    assert len(result) == 1
    mock_repo.get_for_session.assert_called_once()


@pytest.mark.asyncio
async def test_update_selection():
    """Test updating a selection's status."""
    from app.services.activity_service import ActivityService

    mock_repo = AsyncMock()
    mock_selection = MagicMock()
    mock_selection.id = uuid4()
    mock_selection.dwa_id = "4.A.1.a.1"
    mock_selection.selected = False
    mock_selection.user_modified = True
    mock_repo.update_selection.return_value = mock_selection

    service = ActivityService(selection_repository=mock_repo)
    result = await service.update_selection(mock_selection.id, False)

    assert result is not None
    assert result["selected"] == False
    mock_repo.update_selection.assert_called_once()


@pytest.mark.asyncio
async def test_bulk_select():
    """Test bulk selecting/deselecting activities."""
    from app.services.activity_service import ActivityService

    mock_repo = AsyncMock()
    mock_selection = MagicMock()
    mock_selection.id = uuid4()
    mock_selection.selected = False
    mock_repo.get_for_session.return_value = [mock_selection]

    service = ActivityService(selection_repository=mock_repo)
    result = await service.bulk_select(uuid4(), select_all=True)

    assert "updated_count" in result
    assert result["updated_count"] == 1
