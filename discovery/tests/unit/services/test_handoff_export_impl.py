# discovery/tests/unit/services/test_handoff_export_impl.py
"""Unit tests for handoff and export services."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4


@pytest.mark.asyncio
async def test_create_handoff_bundle():
    """Test creating handoff bundle."""
    from app.services.handoff_service import HandoffService

    mock_candidate_repo = AsyncMock()
    mock_session_repo = AsyncMock()

    mock_candidate = MagicMock()
    mock_candidate.id = uuid4()
    mock_candidate.name = "Invoice Agent"
    mock_candidate.description = "Automates invoice processing"
    mock_candidate.estimated_impact = 0.85
    mock_candidate.selected_for_build = True
    mock_candidate.priority_tier = MagicMock()
    mock_candidate.priority_tier.value = "now"
    mock_candidate.role_mapping_id = uuid4()
    mock_candidate_repo.get_for_session.return_value = [mock_candidate]

    mock_session = MagicMock()
    mock_session.id = uuid4()
    mock_session_repo.get_by_id.return_value = mock_session

    service = HandoffService(
        candidate_repository=mock_candidate_repo,
        session_repository=mock_session_repo,
    )

    result = await service.create_handoff_bundle(uuid4())

    assert result is not None
    assert "candidates" in result
    assert len(result["candidates"]) == 1


@pytest.mark.asyncio
async def test_handoff_no_candidates_selected():
    """Test handoff when no candidates are selected."""
    from app.services.handoff_service import HandoffService

    mock_candidate_repo = AsyncMock()

    mock_candidate = MagicMock()
    mock_candidate.selected_for_build = False
    mock_candidate_repo.get_for_session.return_value = [mock_candidate]

    service = HandoffService(candidate_repository=mock_candidate_repo)
    result = await service.create_handoff_bundle(uuid4())

    assert result is not None
    assert "error" in result


def test_export_service_exists():
    """Test ExportService is importable."""
    from app.services.export_service import ExportService
    assert ExportService is not None


@pytest.mark.asyncio
async def test_export_json():
    """Test JSON export."""
    from app.services.export_service import ExportService

    mock_session_repo = AsyncMock()
    mock_analysis_repo = AsyncMock()
    mock_candidate_repo = AsyncMock()

    mock_session = MagicMock()
    mock_session.id = uuid4()
    mock_session.created_at = MagicMock()
    mock_session.created_at.isoformat.return_value = "2026-02-01T00:00:00"
    mock_session.status = MagicMock()
    mock_session.status.value = "completed"
    mock_session_repo.get_by_id.return_value = mock_session

    mock_analysis_repo.get_for_session.return_value = []
    mock_candidate_repo.get_for_session.return_value = []

    service = ExportService(
        session_repository=mock_session_repo,
        analysis_repository=mock_analysis_repo,
        candidate_repository=mock_candidate_repo,
    )

    result = await service.export_json(mock_session.id)

    assert result is not None
    assert "session_id" in result


@pytest.mark.asyncio
async def test_export_csv():
    """Test CSV export."""
    from app.services.export_service import ExportService

    mock_session_repo = AsyncMock()
    mock_analysis_repo = AsyncMock()

    mock_result = MagicMock()
    mock_result.dimension = MagicMock()
    mock_result.dimension.value = "role"
    mock_result.dimension_value = "Engineer"
    mock_result.ai_exposure_score = 0.75
    mock_result.impact_score = 0.8
    mock_result.priority_score = 0.77
    mock_analysis_repo.get_for_session.return_value = [mock_result]

    service = ExportService(
        session_repository=mock_session_repo,
        analysis_repository=mock_analysis_repo,
    )

    result = await service.export_csv(uuid4())

    assert result is not None
    assert "dimension" in result
    assert "Engineer" in result
