# discovery/tests/unit/services/test_roadmap_service_impl.py
"""Unit tests for implemented roadmap service."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4


@pytest.mark.asyncio
async def test_generate_candidates():
    """Test generating agentification candidates."""
    from app.services.roadmap_service import RoadmapService

    mock_candidate_repo = AsyncMock()
    mock_analysis_repo = AsyncMock()

    # Mock analysis results
    mock_result = MagicMock()
    mock_result.id = uuid4()
    mock_result.role_mapping_id = uuid4()
    mock_result.dimension_value = "Data Entry Clerk"
    mock_result.priority_score = 0.85
    mock_result.complexity_score = 0.2
    mock_result.ai_exposure_score = 0.8
    mock_result.breakdown = {"priority_tier": "now"}
    mock_analysis_repo.get_for_session.return_value = [mock_result]

    mock_candidate = MagicMock()
    mock_candidate.id = uuid4()
    mock_candidate.name = "Data Entry Agent"
    mock_candidate.description = "AI agent description"
    mock_candidate.priority_tier = MagicMock()
    mock_candidate.priority_tier.value = "now"
    mock_candidate.estimated_impact = 0.85
    mock_candidate_repo.create.return_value = mock_candidate

    service = RoadmapService(
        candidate_repository=mock_candidate_repo,
        analysis_repository=mock_analysis_repo,
    )

    result = await service.generate_candidates(uuid4())
    assert len(result) > 0


@pytest.mark.asyncio
async def test_get_candidates():
    """Test getting roadmap candidates."""
    from app.services.roadmap_service import RoadmapService

    mock_repo = AsyncMock()
    mock_candidate = MagicMock()
    mock_candidate.id = uuid4()
    mock_candidate.name = "Invoice Agent"
    mock_candidate.description = "Process invoices"
    mock_candidate.priority_tier = MagicMock()
    mock_candidate.priority_tier.value = "now"
    mock_candidate.estimated_impact = 0.85
    mock_candidate.selected_for_build = False
    mock_repo.get_for_session.return_value = [mock_candidate]

    service = RoadmapService(candidate_repository=mock_repo)
    result = await service.get_candidates(uuid4())

    assert len(result) == 1
    assert result[0]["name"] == "Invoice Agent"


@pytest.mark.asyncio
async def test_update_tier():
    """Test updating candidate tier."""
    from app.services.roadmap_service import RoadmapService

    mock_repo = AsyncMock()
    mock_candidate = MagicMock()
    mock_candidate.id = uuid4()
    mock_candidate.name = "Test Agent"
    mock_candidate.priority_tier = MagicMock()
    mock_candidate.priority_tier.value = "next_quarter"
    mock_repo.update_tier.return_value = mock_candidate

    service = RoadmapService(candidate_repository=mock_repo)
    result = await service.update_tier(mock_candidate.id, "next_quarter")

    assert result is not None
    assert result["priority_tier"] == "next_quarter"


@pytest.mark.asyncio
async def test_select_for_build():
    """Test selecting candidate for build."""
    from app.services.roadmap_service import RoadmapService

    mock_repo = AsyncMock()
    mock_candidate = MagicMock()
    mock_candidate.id = uuid4()
    mock_candidate.name = "Test Agent"
    mock_candidate.selected_for_build = True
    mock_repo.select_for_build.return_value = mock_candidate

    service = RoadmapService(candidate_repository=mock_repo)
    result = await service.select_for_build(mock_candidate.id, True)

    assert result is not None
    assert result["selected_for_build"] is True
