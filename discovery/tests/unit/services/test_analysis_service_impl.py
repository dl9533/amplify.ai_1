# discovery/tests/unit/services/test_analysis_service_impl.py
"""Unit tests for implemented analysis service."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4


@pytest.mark.asyncio
async def test_trigger_analysis():
    """Test triggering analysis for a session."""
    from app.services.analysis_service import AnalysisService

    mock_analysis_repo = AsyncMock()
    mock_mapping_repo = AsyncMock()
    mock_selection_repo = AsyncMock()

    # Mock role mappings
    mock_mapping = MagicMock()
    mock_mapping.id = uuid4()
    mock_mapping.source_role = "Engineer"
    mock_mapping.onet_code = "15-1252.00"
    mock_mapping.row_count = 50
    mock_mapping_repo.get_for_session.return_value = [mock_mapping]

    # Mock activity selections
    mock_selection = MagicMock()
    mock_selection.dwa_id = "4.A.1.a.1"
    mock_selection.selected = True
    mock_selection_repo.get_for_role_mapping.return_value = [mock_selection]

    mock_analysis_repo.save_results.return_value = []

    service = AnalysisService(
        analysis_repository=mock_analysis_repo,
        role_mapping_repository=mock_mapping_repo,
        activity_selection_repository=mock_selection_repo,
    )

    session_id = uuid4()
    result = await service.trigger_analysis(session_id)

    assert result is not None
    assert "status" in result


@pytest.mark.asyncio
async def test_get_by_dimension():
    """Test getting analysis results by dimension."""
    from app.services.analysis_service import AnalysisService
    from app.schemas.analysis import AnalysisDimension
    from app.models.discovery_analysis import AnalysisDimension as DBDimension

    mock_repo = AsyncMock()
    mock_result = MagicMock()
    mock_result.id = uuid4()
    mock_result.dimension = DBDimension.ROLE
    mock_result.dimension_value = "Engineer"
    mock_result.ai_exposure_score = 0.75
    mock_result.impact_score = 0.8
    mock_result.complexity_score = 0.25
    mock_result.priority_score = 0.78
    mock_result.breakdown = {"priority_tier": "now"}
    mock_repo.get_for_session.return_value = [mock_result]

    service = AnalysisService(analysis_repository=mock_repo)
    result = await service.get_by_dimension(uuid4(), AnalysisDimension.ROLE)

    assert result is not None
    assert "results" in result


@pytest.mark.asyncio
async def test_get_all_dimensions():
    """Test getting summary of all dimensions."""
    from app.services.analysis_service import AnalysisService
    from app.models.discovery_analysis import AnalysisDimension as DBDimension

    mock_repo = AsyncMock()
    mock_result = MagicMock()
    mock_result.dimension = DBDimension.ROLE
    mock_result.ai_exposure_score = 0.75
    mock_repo.get_for_session.return_value = [mock_result]

    service = AnalysisService(analysis_repository=mock_repo)
    result = await service.get_all_dimensions(uuid4())

    assert result is not None
    assert "role" in result


@pytest.mark.asyncio
async def test_trigger_analysis_no_mappings():
    """Test triggering analysis with no mappings."""
    from app.services.analysis_service import AnalysisService

    mock_analysis_repo = AsyncMock()
    mock_mapping_repo = AsyncMock()
    mock_selection_repo = AsyncMock()

    mock_mapping_repo.get_for_session.return_value = []

    service = AnalysisService(
        analysis_repository=mock_analysis_repo,
        role_mapping_repository=mock_mapping_repo,
        activity_selection_repository=mock_selection_repo,
    )

    result = await service.trigger_analysis(uuid4())

    assert result is not None
    assert result["status"] == "error"
