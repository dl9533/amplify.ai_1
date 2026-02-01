# backend/tests/unit/modules/discovery/test_session_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.modules.discovery.services.session_service import DiscoverySessionService
from app.modules.discovery.enums import SessionStatus, AnalysisDimension, PriorityTier


@pytest.fixture
def mock_session_repo():
    return AsyncMock()


@pytest.fixture
def mock_upload_repo():
    return AsyncMock()


@pytest.fixture
def mock_role_mapping_repo():
    return AsyncMock()


@pytest.fixture
def mock_activity_selection_repo():
    return AsyncMock()


@pytest.fixture
def mock_analysis_result_repo():
    return AsyncMock()


@pytest.fixture
def mock_candidate_repo():
    return AsyncMock()


@pytest.fixture
def session_service(
    mock_session_repo,
    mock_upload_repo,
    mock_role_mapping_repo,
    mock_activity_selection_repo,
    mock_analysis_result_repo,
    mock_candidate_repo
):
    return DiscoverySessionService(
        session_repo=mock_session_repo,
        upload_repo=mock_upload_repo,
        role_mapping_repo=mock_role_mapping_repo,
        activity_selection_repo=mock_activity_selection_repo,
        analysis_result_repo=mock_analysis_result_repo,
        candidate_repo=mock_candidate_repo
    )


@pytest.mark.asyncio
async def test_create_session(session_service, mock_session_repo):
    """Should create a new discovery session."""
    user_id = uuid4()
    org_id = uuid4()

    mock_session = MagicMock()
    mock_session.id = uuid4()
    mock_session.user_id = user_id
    mock_session.organization_id = org_id
    mock_session.status = SessionStatus.DRAFT
    mock_session.current_step = 1
    mock_session_repo.create.return_value = mock_session

    result = await session_service.create_session(user_id=user_id, organization_id=org_id)

    mock_session_repo.create.assert_called_once_with(user_id=user_id, organization_id=org_id)
    assert result.status == SessionStatus.DRAFT
    assert result.current_step == 1


@pytest.mark.asyncio
async def test_get_session(session_service, mock_session_repo):
    """Should retrieve a session by ID."""
    session_id = uuid4()
    mock_session = MagicMock()
    mock_session.id = session_id
    mock_session_repo.get_by_id.return_value = mock_session

    result = await session_service.get_session(session_id)

    mock_session_repo.get_by_id.assert_called_once_with(session_id)
    assert result.id == session_id


@pytest.mark.asyncio
async def test_advance_step(session_service, mock_session_repo):
    """Should advance session to next step."""
    session_id = uuid4()

    mock_session = MagicMock()
    mock_session.current_step = 1
    mock_session_repo.get_by_id.return_value = mock_session

    updated_session = MagicMock()
    updated_session.current_step = 2
    mock_session_repo.update_step.return_value = updated_session

    result = await session_service.advance_step(session_id)

    mock_session_repo.update_step.assert_called_once_with(session_id, step=2)
    assert result.current_step == 2


@pytest.mark.asyncio
async def test_advance_step_when_session_not_found(session_service, mock_session_repo):
    """Should return None when session is not found."""
    session_id = uuid4()
    mock_session_repo.get_by_id.return_value = None

    result = await session_service.advance_step(session_id)

    assert result is None
    mock_session_repo.update_step.assert_not_called()


@pytest.mark.asyncio
async def test_advance_step_updates_status_to_in_progress(session_service, mock_session_repo):
    """Should update status to IN_PROGRESS when advancing from step 1."""
    session_id = uuid4()

    mock_session = MagicMock()
    mock_session.current_step = 1
    mock_session.status = SessionStatus.DRAFT
    mock_session_repo.get_by_id.return_value = mock_session

    await session_service.advance_step(session_id)

    mock_session_repo.update_status.assert_called_once_with(session_id, SessionStatus.IN_PROGRESS)


@pytest.mark.asyncio
async def test_go_to_step(session_service, mock_session_repo):
    """Should allow going back to a previous step."""
    session_id = uuid4()

    mock_session = MagicMock()
    mock_session.current_step = 4
    mock_session_repo.get_by_id.return_value = mock_session

    updated_session = MagicMock()
    updated_session.current_step = 2
    mock_session_repo.update_step.return_value = updated_session

    result = await session_service.go_to_step(session_id, step=2)

    mock_session_repo.update_step.assert_called_once_with(session_id, step=2)
    assert result.current_step == 2


@pytest.mark.asyncio
async def test_go_to_step_when_session_not_found(session_service, mock_session_repo):
    """Should return None when session is not found."""
    session_id = uuid4()
    mock_session_repo.get_by_id.return_value = None

    result = await session_service.go_to_step(session_id, step=3)

    assert result is None
    mock_session_repo.update_step.assert_not_called()


@pytest.mark.asyncio
async def test_go_to_step_rejects_invalid_step(session_service, mock_session_repo):
    """Should reject invalid step numbers."""
    session_id = uuid4()

    mock_session = MagicMock()
    mock_session.current_step = 2
    mock_session_repo.get_by_id.return_value = mock_session

    with pytest.raises(ValueError, match="Step must be between 1 and 5"):
        await session_service.go_to_step(session_id, step=6)

    mock_session_repo.update_step.assert_not_called()


@pytest.mark.asyncio
async def test_go_to_step_with_step_zero(session_service, mock_session_repo):
    """Should reject step < 1."""
    session_id = uuid4()

    with pytest.raises(ValueError, match="Step must be between 1 and 5"):
        await session_service.go_to_step(session_id, step=0)

    mock_session_repo.update_step.assert_not_called()


@pytest.mark.asyncio
async def test_complete_session(session_service, mock_session_repo):
    """Should mark session as completed."""
    session_id = uuid4()

    mock_session = MagicMock()
    mock_session.current_step = 5
    mock_session_repo.get_by_id.return_value = mock_session

    updated_session = MagicMock()
    updated_session.status = SessionStatus.COMPLETED
    mock_session_repo.update_status.return_value = updated_session

    result = await session_service.complete_session(session_id)

    mock_session_repo.update_status.assert_called_once_with(session_id, SessionStatus.COMPLETED)
    assert result.status == SessionStatus.COMPLETED


@pytest.mark.asyncio
async def test_archive_session(session_service, mock_session_repo):
    """Should archive a session."""
    session_id = uuid4()

    updated_session = MagicMock()
    updated_session.status = SessionStatus.ARCHIVED
    mock_session_repo.update_status.return_value = updated_session

    result = await session_service.archive_session(session_id)

    mock_session_repo.update_status.assert_called_once_with(session_id, SessionStatus.ARCHIVED)
    assert result.status == SessionStatus.ARCHIVED


@pytest.mark.asyncio
async def test_get_session_summary(session_service, mock_session_repo, mock_upload_repo, mock_role_mapping_repo, mock_candidate_repo):
    """Should return a summary of the session state."""
    session_id = uuid4()

    mock_session = MagicMock()
    mock_session.id = session_id
    mock_session.current_step = 3
    mock_session.status = SessionStatus.IN_PROGRESS
    mock_session_repo.get_by_id.return_value = mock_session

    mock_upload = MagicMock()
    mock_upload.row_count = 1500
    mock_upload_repo.get_latest_for_session.return_value = mock_upload

    mock_role_mapping_repo.get_by_session_id.return_value = [MagicMock(), MagicMock(), MagicMock()]

    mock_candidate_repo.get_by_session_id.return_value = [MagicMock(), MagicMock()]

    summary = await session_service.get_session_summary(session_id)

    assert summary["session_id"] == session_id
    assert summary["exists"] is True
    assert summary["current_step"] == 3
    assert summary["status"] == SessionStatus.IN_PROGRESS
    assert summary["row_count"] == 1500
    assert summary["role_mapping_count"] == 3
    assert summary["candidate_count"] == 2


@pytest.mark.asyncio
async def test_get_session_summary_when_session_not_found(session_service, mock_session_repo, mock_upload_repo, mock_role_mapping_repo, mock_candidate_repo):
    """Should return a dict indicating session doesn't exist when not found."""
    session_id = uuid4()
    mock_session_repo.get_by_id.return_value = None

    summary = await session_service.get_session_summary(session_id)

    assert summary["session_id"] == session_id
    assert summary["exists"] is False
    assert "current_step" not in summary
    assert "status" not in summary
    # Should not call other repos when session doesn't exist
    mock_upload_repo.get_latest_for_session.assert_not_called()
    mock_role_mapping_repo.get_by_session_id.assert_not_called()
    mock_candidate_repo.get_by_session_id.assert_not_called()


@pytest.mark.asyncio
async def test_register_upload(session_service, mock_upload_repo, mock_session_repo):
    """Should register an upload and update session status."""
    session_id = uuid4()

    mock_session = MagicMock()
    mock_session.status = SessionStatus.DRAFT
    mock_session_repo.get_by_id.return_value = mock_session

    mock_upload = MagicMock()
    mock_upload.id = uuid4()
    mock_upload_repo.create.return_value = mock_upload

    result = await session_service.register_upload(
        session_id=session_id,
        file_name="hr_data.xlsx",
        file_url="s3://bucket/hr_data.xlsx",
        row_count=1500,
        detected_schema={"columns": ["A", "B"]}
    )

    mock_upload_repo.create.assert_called_once()
    assert result is not None


@pytest.mark.asyncio
async def test_create_role_mapping(session_service, mock_role_mapping_repo):
    """Should create a role mapping via the service."""
    session_id = uuid4()

    mock_mapping = MagicMock()
    mock_mapping.id = uuid4()
    mock_mapping.source_role = "Software Engineer"
    mock_mapping.onet_code = "15-1252.00"
    mock_role_mapping_repo.create.return_value = mock_mapping

    result = await session_service.create_role_mapping(
        session_id=session_id,
        source_role="Software Engineer",
        onet_code="15-1252.00",
        confidence_score=0.92,
        row_count=45
    )

    mock_role_mapping_repo.create.assert_called_once()
    assert result.source_role == "Software Engineer"


@pytest.mark.asyncio
async def test_bulk_create_activity_selections(session_service, mock_activity_selection_repo):
    """Should bulk create activity selections for a role mapping."""
    session_id = uuid4()
    role_mapping_id = uuid4()
    dwa_ids = ["4.A.1.a.1.I01", "4.A.1.a.1.I02", "4.A.2.a.1.I01"]

    mock_selections = [MagicMock() for _ in dwa_ids]
    mock_activity_selection_repo.bulk_create.return_value = mock_selections

    result = await session_service.bulk_create_activity_selections(
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        dwa_ids=dwa_ids
    )

    mock_activity_selection_repo.bulk_create.assert_called_once()
    assert len(result) == 3


@pytest.mark.asyncio
async def test_store_analysis_results(session_service, mock_analysis_result_repo):
    """Should store analysis results for multiple dimensions."""
    session_id = uuid4()
    role_mapping_id = uuid4()

    results_data = [
        {"dimension": AnalysisDimension.ROLE, "dimension_value": "Engineer", "ai_exposure_score": 0.85, "priority_score": 0.80},
        {"dimension": AnalysisDimension.DEPARTMENT, "dimension_value": "IT", "ai_exposure_score": 0.78, "priority_score": 0.75},
    ]

    mock_results = [MagicMock() for _ in results_data]
    mock_analysis_result_repo.create.side_effect = mock_results

    result = await session_service.store_analysis_results(
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        results=results_data
    )

    assert mock_analysis_result_repo.create.call_count == 2
    assert len(result) == 2


@pytest.mark.asyncio
async def test_store_analysis_results_with_empty_list(session_service, mock_analysis_result_repo):
    """Should return empty list when given empty results."""
    session_id = uuid4()
    role_mapping_id = uuid4()

    result = await session_service.store_analysis_results(
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        results=[]
    )

    assert result == []
    mock_analysis_result_repo.create.assert_not_called()


@pytest.mark.asyncio
async def test_create_candidate(session_service, mock_candidate_repo):
    """Should create an agentification candidate."""
    session_id = uuid4()
    role_mapping_id = uuid4()

    mock_candidate = MagicMock()
    mock_candidate.id = uuid4()
    mock_candidate.name = "Data Entry Agent"
    mock_candidate.priority_tier = PriorityTier.NOW
    mock_candidate_repo.create.return_value = mock_candidate

    result = await session_service.create_candidate(
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        name="Data Entry Agent",
        description="Automates data entry tasks",
        priority_tier=PriorityTier.NOW,
        estimated_impact=0.85
    )

    mock_candidate_repo.create.assert_called_once()
    assert result.name == "Data Entry Agent"


@pytest.mark.asyncio
async def test_select_candidates_for_build(session_service, mock_candidate_repo):
    """Should select multiple candidates for build."""
    candidate_ids = [uuid4(), uuid4(), uuid4()]

    mock_candidates = [MagicMock(selected_for_build=True) for _ in candidate_ids]
    mock_candidate_repo.select_for_build.side_effect = mock_candidates

    result = await session_service.select_candidates_for_build(candidate_ids)

    assert mock_candidate_repo.select_for_build.call_count == 3
    assert len(result) == 3


@pytest.mark.asyncio
async def test_select_candidates_for_build_empty_list(session_service, mock_candidate_repo):
    """Should return empty list when given empty input."""
    result = await session_service.select_candidates_for_build([])

    assert result == []
    mock_candidate_repo.select_for_build.assert_not_called()


@pytest.mark.asyncio
async def test_get_handoff_bundle_when_session_not_found(
    session_service,
    mock_session_repo,
    mock_candidate_repo,
    mock_role_mapping_repo,
    mock_analysis_result_repo
):
    """Should return empty candidates list when session not found."""
    session_id = uuid4()
    mock_session_repo.get_by_id.return_value = None

    bundle = await session_service.get_handoff_bundle(session_id)

    assert bundle["session_id"] == session_id
    assert bundle["candidates"] == []
    # Should not call other repos when session doesn't exist
    mock_candidate_repo.get_selected_for_build.assert_not_called()
    mock_role_mapping_repo.get_by_id.assert_not_called()
    mock_analysis_result_repo.get_by_role_mapping_id.assert_not_called()


@pytest.mark.asyncio
async def test_get_handoff_bundle(session_service, mock_session_repo, mock_candidate_repo, mock_role_mapping_repo, mock_analysis_result_repo):
    """Should prepare a handoff bundle for intake with complete candidate data."""
    session_id = uuid4()

    mock_session = MagicMock()
    mock_session.id = session_id
    mock_session_repo.get_by_id.return_value = mock_session

    mock_candidates = [
        MagicMock(
            id=uuid4(),
            name="Agent1",
            description="Test agent description",
            priority_tier=PriorityTier.NOW,
            estimated_impact=0.85,
            selected_for_build=True,
            role_mapping_id=uuid4()
        ),
        MagicMock(
            id=uuid4(),
            name="Agent2",
            description="Another agent",
            priority_tier=PriorityTier.NEXT_QUARTER,
            estimated_impact=0.72,
            selected_for_build=True,
            role_mapping_id=uuid4()
        ),
    ]
    mock_candidate_repo.get_selected_for_build.return_value = mock_candidates

    mock_role_mapping_repo.get_by_id.return_value = MagicMock(source_role="Engineer", onet_code="15-1252.00")

    mock_analysis_result = MagicMock(
        dimension=AnalysisDimension.ROLE,
        dimension_value="Engineer",
        ai_exposure_score=0.85,
        impact_score=0.80,
        complexity_score=0.60,
        priority_score=0.75,
        breakdown={"detail": "test"}
    )
    mock_analysis_result_repo.get_by_role_mapping_id.return_value = [mock_analysis_result]

    bundle = await session_service.get_handoff_bundle(session_id)

    assert "session_id" in bundle
    assert "candidates" in bundle
    assert len(bundle["candidates"]) == 2

    # Verify complete candidate data is included
    candidate_bundle = bundle["candidates"][0]
    assert "id" in candidate_bundle
    assert "name" in candidate_bundle
    assert "description" in candidate_bundle
    assert "priority_tier" in candidate_bundle
    assert "estimated_impact" in candidate_bundle
    assert "role_mapping" in candidate_bundle
    assert "analysis_results" in candidate_bundle

    # Verify full analysis result fields
    analysis_result = candidate_bundle["analysis_results"][0]
    assert "dimension" in analysis_result
    assert "dimension_value" in analysis_result
    assert "ai_exposure_score" in analysis_result
    assert "impact_score" in analysis_result
    assert "complexity_score" in analysis_result
    assert "priority_score" in analysis_result
    assert "breakdown" in analysis_result


@pytest.mark.asyncio
async def test_list_user_sessions(session_service, mock_session_repo):
    """Should list all sessions for a user."""
    user_id = uuid4()

    mock_sessions = [MagicMock(), MagicMock()]
    mock_session_repo.list_for_user.return_value = mock_sessions

    result = await session_service.list_user_sessions(user_id)

    mock_session_repo.list_for_user.assert_called_once_with(user_id)
    assert len(result) == 2
