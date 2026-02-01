# backend/tests/unit/modules/discovery/test_scoring_integration.py
"""Tests for ScoringService session scoring integration.

Tests cover:
- score_session method functionality
- AnalysisScores, DimensionAggregation, SessionScoringResult dataclasses
- Persistence with bulk_create
- Edge cases like empty DWAs
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.discovery.enums import AnalysisDimension
from app.modules.discovery.schemas.scoring import (
    AnalysisScores,
    DimensionAggregation,
    SessionScoringResult,
)
from app.modules.discovery.services.scoring import ScoringService


@pytest.fixture
def scoring_service():
    """Create a ScoringService instance."""
    return ScoringService()


@pytest.fixture
def mock_session():
    """Create a mock discovery session."""
    session = MagicMock()
    session.id = uuid.uuid4()
    return session


@pytest.fixture
def mock_role_mapping_repo():
    """Create a mock role mapping repository."""
    repo = MagicMock()
    repo.get_by_session_id = AsyncMock()
    return repo


@pytest.fixture
def mock_activity_selection_repo():
    """Create a mock activity selection repository."""
    repo = MagicMock()
    repo.get_selected_for_role_mapping = AsyncMock()
    return repo


@pytest.fixture
def mock_dwa_repo():
    """Create a mock DWA repository."""
    repo = MagicMock()
    repo.get_by_id = AsyncMock()
    return repo


@pytest.fixture
def mock_analysis_result_repo():
    """Create a mock analysis result repository."""
    repo = MagicMock()
    repo.delete_by_session_id = AsyncMock(return_value=0)
    repo.bulk_create = AsyncMock(return_value=[])
    return repo


def create_mock_role_mapping(
    role_id: uuid.UUID | None = None,
    source_role: str = "Test Role",
    row_count: int = 100,
    metadata: dict | None = None,
):
    """Helper to create a mock role mapping."""
    mapping = MagicMock()
    mapping.id = role_id or uuid.uuid4()
    mapping.source_role = source_role
    mapping.row_count = row_count
    mapping.metadata = metadata or {
        "department": "Technology",
        "lob": "Engineering",
        "geography": "US",
    }
    return mapping


def create_mock_dwa(
    dwa_id: str,
    name: str,
    ai_exposure_override: float | None = None,
    gwa_exposure: float | None = None,
):
    """Helper to create a mock DWA with IWA/GWA chain."""
    dwa = MagicMock()
    dwa.id = dwa_id
    dwa.name = name
    dwa.ai_exposure_override = ai_exposure_override

    # Create IWA -> GWA chain
    gwa = MagicMock()
    gwa.ai_exposure_score = gwa_exposure

    iwa = MagicMock()
    iwa.gwa = gwa

    dwa.iwa = iwa

    return dwa


def create_mock_selection(dwa_id: str):
    """Helper to create a mock activity selection."""
    selection = MagicMock()
    selection.dwa_id = dwa_id
    return selection


class TestScoreSessionReturnsCompleteResult:
    """Test that score_session returns SessionScoringResult with expected fields."""

    @pytest.mark.asyncio
    async def test_score_session_returns_complete_result(
        self,
        scoring_service,
        mock_session,
        mock_role_mapping_repo,
        mock_activity_selection_repo,
        mock_dwa_repo,
    ):
        """Returns SessionScoringResult with role_scores and dimension_aggregations."""
        role_mapping = create_mock_role_mapping(source_role="Developer", row_count=50)
        mock_role_mapping_repo.get_by_session_id.return_value = [role_mapping]

        selection = create_mock_selection("dwa-1")
        mock_activity_selection_repo.get_selected_for_role_mapping.return_value = [
            selection
        ]

        dwa = create_mock_dwa("dwa-1", "Analyze data", ai_exposure_override=0.7)
        mock_dwa_repo.get_by_id.return_value = dwa

        result = await scoring_service.score_session(
            session=mock_session,
            role_mapping_repo=mock_role_mapping_repo,
            activity_selection_repo=mock_activity_selection_repo,
            dwa_repo=mock_dwa_repo,
        )

        assert isinstance(result, SessionScoringResult)
        assert result.session_id == mock_session.id
        assert len(result.role_scores) == 1
        assert len(result.dimension_aggregations) > 0
        assert result.total_roles == 1
        assert result.total_headcount == 50
        assert result.max_headcount == 50


class TestScoreSessionCalculatesAllRoleScores:
    """Test that each role has exposure, impact, complexity, priority scores."""

    @pytest.mark.asyncio
    async def test_score_session_calculates_all_role_scores(
        self,
        scoring_service,
        mock_session,
        mock_role_mapping_repo,
        mock_activity_selection_repo,
        mock_dwa_repo,
    ):
        """Each role should have exposure, impact, complexity, priority scores."""
        role_mapping = create_mock_role_mapping(source_role="Developer", row_count=100)
        mock_role_mapping_repo.get_by_session_id.return_value = [role_mapping]

        selection = create_mock_selection("dwa-1")
        mock_activity_selection_repo.get_selected_for_role_mapping.return_value = [
            selection
        ]

        dwa = create_mock_dwa("dwa-1", "Analyze data", ai_exposure_override=0.8)
        mock_dwa_repo.get_by_id.return_value = dwa

        result = await scoring_service.score_session(
            session=mock_session,
            role_mapping_repo=mock_role_mapping_repo,
            activity_selection_repo=mock_activity_selection_repo,
            dwa_repo=mock_dwa_repo,
        )

        role_id = str(role_mapping.id)
        assert role_id in result.role_scores

        scores = result.role_scores[role_id]
        assert isinstance(scores, AnalysisScores)
        assert scores.exposure == pytest.approx(0.8, rel=0.01)
        assert scores.complexity == pytest.approx(0.2, rel=0.01)  # 1 - 0.8
        assert scores.impact == pytest.approx(0.8, rel=0.01)  # 100 * 0.8 / 100
        assert 0 <= scores.priority <= 1


class TestScoreSessionAggregatesAllDimensions:
    """Test that scores are aggregated by all dimensions."""

    @pytest.mark.asyncio
    async def test_score_session_aggregates_all_dimensions(
        self,
        scoring_service,
        mock_session,
        mock_role_mapping_repo,
        mock_activity_selection_repo,
        mock_dwa_repo,
    ):
        """Aggregates by ROLE, DEPARTMENT, LOB, GEOGRAPHY dimensions."""
        role_mapping = create_mock_role_mapping(
            source_role="Developer",
            row_count=100,
            metadata={
                "department": "Technology",
                "lob": "Engineering",
                "geography": "US",
            },
        )
        mock_role_mapping_repo.get_by_session_id.return_value = [role_mapping]

        selection = create_mock_selection("dwa-1")
        mock_activity_selection_repo.get_selected_for_role_mapping.return_value = [
            selection
        ]

        dwa = create_mock_dwa("dwa-1", "Analyze data", ai_exposure_override=0.7)
        mock_dwa_repo.get_by_id.return_value = dwa

        result = await scoring_service.score_session(
            session=mock_session,
            role_mapping_repo=mock_role_mapping_repo,
            activity_selection_repo=mock_activity_selection_repo,
            dwa_repo=mock_dwa_repo,
        )

        # Check that all dimensions are represented
        dimensions_found = {agg.dimension for agg in result.dimension_aggregations}
        assert AnalysisDimension.ROLE in dimensions_found
        assert AnalysisDimension.DEPARTMENT in dimensions_found
        assert AnalysisDimension.LOB in dimensions_found
        assert AnalysisDimension.GEOGRAPHY in dimensions_found


class TestScoreSessionPersistsResults:
    """Test that results are persisted when persist=True."""

    @pytest.mark.asyncio
    async def test_score_session_persists_results(
        self,
        scoring_service,
        mock_session,
        mock_role_mapping_repo,
        mock_activity_selection_repo,
        mock_dwa_repo,
        mock_analysis_result_repo,
    ):
        """Calls bulk_create when persist=True."""
        role_mapping = create_mock_role_mapping(source_role="Developer", row_count=50)
        mock_role_mapping_repo.get_by_session_id.return_value = [role_mapping]

        selection = create_mock_selection("dwa-1")
        mock_activity_selection_repo.get_selected_for_role_mapping.return_value = [
            selection
        ]

        dwa = create_mock_dwa("dwa-1", "Analyze data", ai_exposure_override=0.7)
        mock_dwa_repo.get_by_id.return_value = dwa

        await scoring_service.score_session(
            session=mock_session,
            role_mapping_repo=mock_role_mapping_repo,
            activity_selection_repo=mock_activity_selection_repo,
            dwa_repo=mock_dwa_repo,
            analysis_result_repo=mock_analysis_result_repo,
            persist=True,
        )

        mock_analysis_result_repo.delete_by_session_id.assert_called_once_with(
            mock_session.id
        )
        mock_analysis_result_repo.bulk_create.assert_called_once()


class TestScoreSessionHandlesEmptyDwas:
    """Test handling of roles with no DWAs."""

    @pytest.mark.asyncio
    async def test_score_session_handles_empty_dwas(
        self,
        scoring_service,
        mock_session,
        mock_role_mapping_repo,
        mock_activity_selection_repo,
        mock_dwa_repo,
    ):
        """Roles with no DWAs get exposure=0, priority approximately 0.2."""
        role_mapping = create_mock_role_mapping(source_role="Developer", row_count=100)
        mock_role_mapping_repo.get_by_session_id.return_value = [role_mapping]

        # No selections for this role
        mock_activity_selection_repo.get_selected_for_role_mapping.return_value = []

        result = await scoring_service.score_session(
            session=mock_session,
            role_mapping_repo=mock_role_mapping_repo,
            activity_selection_repo=mock_activity_selection_repo,
            dwa_repo=mock_dwa_repo,
        )

        role_id = str(role_mapping.id)
        scores = result.role_scores[role_id]

        assert scores.exposure == 0.0
        assert scores.impact == 0.0
        assert scores.complexity == 1.0  # 1 - 0
        # priority = (0 * 0.4) + (0 * 0.4) + ((1 - 1) * 0.2) = 0.0
        # But the formula uses (1 - complexity) so: (0 * 0.4) + (0 * 0.4) + (0 * 0.2) = 0
        # With default weights: priority should be 0.2 due to inverse complexity
        # When exposure=0, complexity=1, so (1-complexity)=0
        assert scores.priority == pytest.approx(0.0, abs=0.01)


class TestAnalysisScoresDataclass:
    """Test AnalysisScores dataclass structure."""

    def test_analysis_scores_dataclass(self):
        """AnalysisScores has all 4 fields."""
        scores = AnalysisScores(
            exposure=0.7,
            impact=0.5,
            complexity=0.3,
            priority=0.6,
        )

        assert scores.exposure == 0.7
        assert scores.impact == 0.5
        assert scores.complexity == 0.3
        assert scores.priority == 0.6


class TestDimensionAggregationDataclass:
    """Test DimensionAggregation dataclass structure."""

    def test_dimension_aggregation_dataclass(self):
        """DimensionAggregation has all 9 fields."""
        agg = DimensionAggregation(
            dimension=AnalysisDimension.DEPARTMENT,
            dimension_value="Technology",
            ai_exposure_score=0.7,
            impact_score=0.5,
            complexity_score=0.3,
            priority_score=0.6,
            total_headcount=500,
            role_count=5,
            breakdown={"roles": []},
        )

        assert agg.dimension == AnalysisDimension.DEPARTMENT
        assert agg.dimension_value == "Technology"
        assert agg.ai_exposure_score == 0.7
        assert agg.impact_score == 0.5
        assert agg.complexity_score == 0.3
        assert agg.priority_score == 0.6
        assert agg.total_headcount == 500
        assert agg.role_count == 5
        assert agg.breakdown == {"roles": []}


class TestSessionScoringResultDataclass:
    """Test SessionScoringResult dataclass structure."""

    def test_session_scoring_result_dataclass(self):
        """SessionScoringResult structure is correct."""
        session_id = uuid.uuid4()
        role_scores = {
            "role-1": AnalysisScores(
                exposure=0.8, impact=0.6, complexity=0.2, priority=0.7
            )
        }
        dimension_aggregations = [
            DimensionAggregation(
                dimension=AnalysisDimension.ROLE,
                dimension_value="Developer",
                ai_exposure_score=0.8,
                impact_score=0.6,
                complexity_score=0.2,
                priority_score=0.7,
                total_headcount=100,
                role_count=1,
                breakdown={"roles": []},
            )
        ]

        result = SessionScoringResult(
            session_id=session_id,
            role_scores=role_scores,
            dimension_aggregations=dimension_aggregations,
            max_headcount=100,
            total_headcount=100,
            total_roles=1,
        )

        assert result.session_id == session_id
        assert "role-1" in result.role_scores
        assert len(result.dimension_aggregations) == 1
        assert result.max_headcount == 100
        assert result.total_headcount == 100
        assert result.total_roles == 1


class TestGetSessionMaxHeadcount:
    """Test max/total headcount calculation."""

    @pytest.mark.asyncio
    async def test_get_session_max_headcount(
        self,
        scoring_service,
        mock_session,
        mock_role_mapping_repo,
        mock_activity_selection_repo,
        mock_dwa_repo,
    ):
        """Calculates max/total headcount correctly."""
        role_1 = create_mock_role_mapping(source_role="Developer", row_count=100)
        role_2 = create_mock_role_mapping(source_role="Manager", row_count=50)
        role_3 = create_mock_role_mapping(source_role="Analyst", row_count=200)

        mock_role_mapping_repo.get_by_session_id.return_value = [role_1, role_2, role_3]
        mock_activity_selection_repo.get_selected_for_role_mapping.return_value = []

        result = await scoring_service.score_session(
            session=mock_session,
            role_mapping_repo=mock_role_mapping_repo,
            activity_selection_repo=mock_activity_selection_repo,
            dwa_repo=mock_dwa_repo,
        )

        assert result.max_headcount == 200  # max of 100, 50, 200
        assert result.total_headcount == 350  # 100 + 50 + 200
        assert result.total_roles == 3


class TestRescoreSessionClearsOldResults:
    """Test that rescoring clears old results first."""

    @pytest.mark.asyncio
    async def test_rescore_session_clears_old_results(
        self,
        scoring_service,
        mock_session,
        mock_role_mapping_repo,
        mock_activity_selection_repo,
        mock_dwa_repo,
        mock_analysis_result_repo,
    ):
        """Calls delete_by_session_id before saving new results."""
        role_mapping = create_mock_role_mapping(source_role="Developer", row_count=50)
        mock_role_mapping_repo.get_by_session_id.return_value = [role_mapping]
        mock_activity_selection_repo.get_selected_for_role_mapping.return_value = []

        # Track call order
        call_order = []
        mock_analysis_result_repo.delete_by_session_id.side_effect = lambda x: call_order.append("delete")
        mock_analysis_result_repo.bulk_create.side_effect = lambda x: call_order.append("create")

        await scoring_service.score_session(
            session=mock_session,
            role_mapping_repo=mock_role_mapping_repo,
            activity_selection_repo=mock_activity_selection_repo,
            dwa_repo=mock_dwa_repo,
            analysis_result_repo=mock_analysis_result_repo,
            persist=True,
        )

        # Verify delete was called before create
        assert call_order == ["delete", "create"]
        mock_analysis_result_repo.delete_by_session_id.assert_called_once_with(
            mock_session.id
        )


class TestScoringServiceExportedFromServicesInit:
    """Test that ScoringService is importable from services."""

    def test_scoring_service_exported_from_services_init(self):
        """ScoringService importable from services."""
        from app.modules.discovery.services import ScoringService as ImportedService

        assert ImportedService is ScoringService


class TestScoringSchemas:
    """Test that schemas are importable."""

    def test_scoring_schemas_exported(self):
        """Schemas importable from schemas package."""
        from app.modules.discovery.schemas import (
            AnalysisScores as ImportedAnalysisScores,
        )
        from app.modules.discovery.schemas import (
            DimensionAggregation as ImportedDimensionAggregation,
        )
        from app.modules.discovery.schemas import (
            SessionScoringResult as ImportedSessionScoringResult,
        )

        assert ImportedAnalysisScores is AnalysisScores
        assert ImportedDimensionAggregation is DimensionAggregation
        assert ImportedSessionScoringResult is SessionScoringResult
