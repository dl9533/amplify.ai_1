"""Tests for analysis router."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers.analysis import router
from app.services.analysis_service import (
    AnalysisService,
    ScoringService,
    get_analysis_service,
    get_scoring_service,
)
from app.schemas.analysis import AnalysisDimension, PriorityTier


@pytest.fixture
def mock_analysis_service():
    """Mock analysis service for testing."""
    service = MagicMock(spec=AnalysisService)
    service.trigger_analysis = AsyncMock()
    service.get_by_dimension = AsyncMock()
    service.get_all_dimensions = AsyncMock()
    return service


@pytest.fixture
def mock_scoring_service():
    """Mock scoring service for testing."""
    service = MagicMock(spec=ScoringService)
    service.score_session = AsyncMock()
    return service


@pytest.fixture
def app(mock_analysis_service, mock_scoring_service):
    """Create test FastAPI app with mocked dependencies."""
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_analysis_service] = lambda: mock_analysis_service
    app.dependency_overrides[get_scoring_service] = lambda: mock_scoring_service
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


class TestTriggerAnalysis:
    """Tests for POST /discovery/sessions/{session_id}/analyze."""

    def test_trigger_analysis_returns_202(self, client, mock_analysis_service):
        """Should trigger analysis and return 202 Accepted with processing status."""
        session_id = uuid4()
        mock_analysis_service.trigger_analysis.return_value = {"status": "processing"}

        response = client.post(f"/discovery/sessions/{session_id}/analyze")

        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "processing"
        mock_analysis_service.trigger_analysis.assert_called_once_with(
            session_id=session_id
        )

    def test_trigger_analysis_session_not_found_returns_404(
        self, client, mock_analysis_service
    ):
        """Should return 404 if session not found."""
        session_id = uuid4()
        mock_analysis_service.trigger_analysis.return_value = None

        response = client.post(f"/discovery/sessions/{session_id}/analyze")

        assert response.status_code == 404
        assert "session" in response.json()["detail"].lower()

    def test_trigger_analysis_validates_uuid(self, client, mock_analysis_service):
        """Should validate session ID is a valid UUID."""
        response = client.post("/discovery/sessions/not-a-uuid/analyze")

        assert response.status_code == 422


class TestGetAnalysisByDimension:
    """Tests for GET /discovery/sessions/{session_id}/analysis/{dimension}."""

    def test_get_analysis_by_dimension_returns_200(
        self, client, mock_analysis_service
    ):
        """Should return analysis results for a specific dimension."""
        session_id = uuid4()
        result_id = uuid4()
        mock_analysis_service.get_by_dimension.return_value = {
            "dimension": "ROLE",
            "results": [
                {
                    "id": str(result_id),
                    "name": "Data Analyst",
                    "ai_exposure_score": 0.75,
                    "impact_score": 0.65,
                    "complexity_score": 0.45,
                    "priority_score": 0.80,
                    "priority_tier": "HIGH",
                }
            ],
        }

        response = client.get(f"/discovery/sessions/{session_id}/analysis/ROLE")

        assert response.status_code == 200
        data = response.json()
        assert data["dimension"] == "ROLE"
        assert len(data["results"]) == 1
        assert data["results"][0]["id"] == str(result_id)
        assert data["results"][0]["name"] == "Data Analyst"
        assert data["results"][0]["ai_exposure_score"] == 0.75
        assert data["results"][0]["impact_score"] == 0.65
        assert data["results"][0]["complexity_score"] == 0.45
        assert data["results"][0]["priority_score"] == 0.80
        assert data["results"][0]["priority_tier"] == "HIGH"
        mock_analysis_service.get_by_dimension.assert_called_once_with(
            session_id=session_id,
            dimension=AnalysisDimension.ROLE,
            priority_tier=None,
        )

    def test_get_analysis_by_dimension_with_priority_filter(
        self, client, mock_analysis_service
    ):
        """Should filter results by priority tier."""
        session_id = uuid4()
        result_id = uuid4()
        mock_analysis_service.get_by_dimension.return_value = {
            "dimension": "DEPARTMENT",
            "results": [
                {
                    "id": str(result_id),
                    "name": "Finance",
                    "ai_exposure_score": 0.85,
                    "impact_score": 0.75,
                    "complexity_score": 0.55,
                    "priority_score": 0.90,
                    "priority_tier": "HIGH",
                }
            ],
        }

        response = client.get(
            f"/discovery/sessions/{session_id}/analysis/DEPARTMENT",
            params={"priority_tier": "HIGH"},
        )

        assert response.status_code == 200
        mock_analysis_service.get_by_dimension.assert_called_once_with(
            session_id=session_id,
            dimension=AnalysisDimension.DEPARTMENT,
            priority_tier=PriorityTier.HIGH,
        )

    def test_get_analysis_by_dimension_all_dimensions(
        self, client, mock_analysis_service
    ):
        """Should accept all valid dimension values."""
        session_id = uuid4()
        mock_analysis_service.get_by_dimension.return_value = {
            "dimension": "TASK",
            "results": [],
        }

        for dimension in ["ROLE", "DEPARTMENT", "LOB", "GEOGRAPHY", "TASK"]:
            response = client.get(
                f"/discovery/sessions/{session_id}/analysis/{dimension}"
            )
            assert response.status_code == 200

    def test_get_analysis_by_dimension_not_found_returns_404(
        self, client, mock_analysis_service
    ):
        """Should return 404 if analysis not yet run."""
        session_id = uuid4()
        mock_analysis_service.get_by_dimension.return_value = None

        response = client.get(f"/discovery/sessions/{session_id}/analysis/ROLE")

        assert response.status_code == 404
        assert "analysis" in response.json()["detail"].lower()

    def test_get_analysis_by_dimension_invalid_dimension_returns_422(
        self, client, mock_analysis_service
    ):
        """Should return 422 for invalid dimension."""
        session_id = uuid4()

        response = client.get(
            f"/discovery/sessions/{session_id}/analysis/INVALID_DIMENSION"
        )

        assert response.status_code == 422

    def test_get_analysis_by_dimension_validates_uuid(
        self, client, mock_analysis_service
    ):
        """Should validate session ID is a valid UUID."""
        response = client.get("/discovery/sessions/not-a-uuid/analysis/ROLE")

        assert response.status_code == 422

    def test_get_analysis_by_dimension_empty_results(
        self, client, mock_analysis_service
    ):
        """Should return empty results list when no results for dimension."""
        session_id = uuid4()
        mock_analysis_service.get_by_dimension.return_value = {
            "dimension": "LOB",
            "results": [],
        }

        response = client.get(f"/discovery/sessions/{session_id}/analysis/LOB")

        assert response.status_code == 200
        data = response.json()
        assert data["dimension"] == "LOB"
        assert data["results"] == []

    def test_get_analysis_by_dimension_all_priority_tiers(
        self, client, mock_analysis_service
    ):
        """Should accept all valid priority tier values."""
        session_id = uuid4()
        mock_analysis_service.get_by_dimension.return_value = {
            "dimension": "ROLE",
            "results": [],
        }

        for tier in ["HIGH", "MEDIUM", "LOW"]:
            response = client.get(
                f"/discovery/sessions/{session_id}/analysis/ROLE",
                params={"priority_tier": tier},
            )
            assert response.status_code == 200


class TestGetAllDimensionsAnalysis:
    """Tests for GET /discovery/sessions/{session_id}/analysis."""

    def test_get_all_dimensions_returns_200(self, client, mock_analysis_service):
        """Should return summary of all dimensions."""
        session_id = uuid4()
        mock_analysis_service.get_all_dimensions.return_value = {
            "ROLE": {"count": 15, "avg_exposure": 0.68},
            "DEPARTMENT": {"count": 8, "avg_exposure": 0.72},
            "LOB": {"count": 5, "avg_exposure": 0.55},
            "GEOGRAPHY": {"count": 3, "avg_exposure": 0.61},
            "TASK": {"count": 120, "avg_exposure": 0.58},
        }

        response = client.get(f"/discovery/sessions/{session_id}/analysis")

        assert response.status_code == 200
        data = response.json()
        assert "ROLE" in data
        assert data["ROLE"]["count"] == 15
        assert data["ROLE"]["avg_exposure"] == 0.68
        assert "DEPARTMENT" in data
        assert data["DEPARTMENT"]["count"] == 8
        assert data["DEPARTMENT"]["avg_exposure"] == 0.72
        assert "LOB" in data
        assert data["LOB"]["count"] == 5
        assert "GEOGRAPHY" in data
        assert data["GEOGRAPHY"]["count"] == 3
        assert "TASK" in data
        assert data["TASK"]["count"] == 120
        mock_analysis_service.get_all_dimensions.assert_called_once_with(
            session_id=session_id
        )

    def test_get_all_dimensions_session_not_found_returns_404(
        self, client, mock_analysis_service
    ):
        """Should return 404 if session not found or analysis not run."""
        session_id = uuid4()
        mock_analysis_service.get_all_dimensions.return_value = None

        response = client.get(f"/discovery/sessions/{session_id}/analysis")

        assert response.status_code == 404
        assert "analysis" in response.json()["detail"].lower()

    def test_get_all_dimensions_validates_uuid(self, client, mock_analysis_service):
        """Should validate session ID is a valid UUID."""
        response = client.get("/discovery/sessions/not-a-uuid/analysis")

        assert response.status_code == 422

    def test_get_all_dimensions_empty_dimensions(self, client, mock_analysis_service):
        """Should handle empty dimension summaries."""
        session_id = uuid4()
        mock_analysis_service.get_all_dimensions.return_value = {
            "ROLE": {"count": 0, "avg_exposure": 0.0},
            "DEPARTMENT": {"count": 0, "avg_exposure": 0.0},
            "LOB": {"count": 0, "avg_exposure": 0.0},
            "GEOGRAPHY": {"count": 0, "avg_exposure": 0.0},
            "TASK": {"count": 0, "avg_exposure": 0.0},
        }

        response = client.get(f"/discovery/sessions/{session_id}/analysis")

        assert response.status_code == 200
        data = response.json()
        assert data["ROLE"]["count"] == 0
        assert data["ROLE"]["avg_exposure"] == 0.0


class TestSchemas:
    """Tests for Pydantic schemas."""

    def test_analysis_dimension_enum_values(self):
        """AnalysisDimension should have all required values."""
        from app.schemas.analysis import AnalysisDimension

        assert AnalysisDimension.ROLE.value == "ROLE"
        assert AnalysisDimension.DEPARTMENT.value == "DEPARTMENT"
        assert AnalysisDimension.LOB.value == "LOB"
        assert AnalysisDimension.GEOGRAPHY.value == "GEOGRAPHY"
        assert AnalysisDimension.TASK.value == "TASK"

    def test_priority_tier_enum_values(self):
        """PriorityTier should have all required values."""
        from app.schemas.analysis import PriorityTier

        assert PriorityTier.HIGH.value == "HIGH"
        assert PriorityTier.MEDIUM.value == "MEDIUM"
        assert PriorityTier.LOW.value == "LOW"

    def test_analysis_result_fields(self):
        """AnalysisResult should have required fields."""
        from app.schemas.analysis import AnalysisResult, PriorityTier

        result_id = uuid4()
        schema = AnalysisResult(
            id=result_id,
            name="Data Analyst",
            ai_exposure_score=0.75,
            impact_score=0.65,
            complexity_score=0.45,
            priority_score=0.80,
            priority_tier=PriorityTier.HIGH,
        )

        assert schema.id == result_id
        assert schema.name == "Data Analyst"
        assert schema.ai_exposure_score == 0.75
        assert schema.impact_score == 0.65
        assert schema.complexity_score == 0.45
        assert schema.priority_score == 0.80
        assert schema.priority_tier == PriorityTier.HIGH

    def test_analysis_result_score_validation(self):
        """AnalysisResult should validate score ranges (0.0-1.0)."""
        from pydantic import ValidationError

        from app.schemas.analysis import AnalysisResult, PriorityTier

        # Valid boundary values
        schema = AnalysisResult(
            id=uuid4(),
            name="Test",
            ai_exposure_score=0.0,
            impact_score=0.0,
            complexity_score=0.0,
            priority_score=0.0,
            priority_tier=PriorityTier.LOW,
        )
        assert schema.ai_exposure_score == 0.0

        schema = AnalysisResult(
            id=uuid4(),
            name="Test",
            ai_exposure_score=1.0,
            impact_score=1.0,
            complexity_score=1.0,
            priority_score=1.0,
            priority_tier=PriorityTier.HIGH,
        )
        assert schema.ai_exposure_score == 1.0

        # Invalid: below 0.0
        with pytest.raises(ValidationError):
            AnalysisResult(
                id=uuid4(),
                name="Test",
                ai_exposure_score=-0.1,
                impact_score=0.5,
                complexity_score=0.5,
                priority_score=0.5,
                priority_tier=PriorityTier.MEDIUM,
            )

        # Invalid: above 1.0
        with pytest.raises(ValidationError):
            AnalysisResult(
                id=uuid4(),
                name="Test",
                ai_exposure_score=1.1,
                impact_score=0.5,
                complexity_score=0.5,
                priority_score=0.5,
                priority_tier=PriorityTier.MEDIUM,
            )

    def test_dimension_analysis_response_fields(self):
        """DimensionAnalysisResponse should have required fields."""
        from app.schemas.analysis import (
            AnalysisDimension,
            AnalysisResult,
            DimensionAnalysisResponse,
            PriorityTier,
        )

        result = AnalysisResult(
            id=uuid4(),
            name="Data Analyst",
            ai_exposure_score=0.75,
            impact_score=0.65,
            complexity_score=0.45,
            priority_score=0.80,
            priority_tier=PriorityTier.HIGH,
        )
        schema = DimensionAnalysisResponse(
            dimension=AnalysisDimension.ROLE,
            results=[result],
        )

        assert schema.dimension == AnalysisDimension.ROLE
        assert len(schema.results) == 1
        assert schema.results[0].name == "Data Analyst"

    def test_dimension_analysis_response_empty_results(self):
        """DimensionAnalysisResponse should allow empty results."""
        from app.schemas.analysis import (
            AnalysisDimension,
            DimensionAnalysisResponse,
        )

        schema = DimensionAnalysisResponse(
            dimension=AnalysisDimension.DEPARTMENT,
            results=[],
        )

        assert schema.results == []

    def test_dimension_summary_fields(self):
        """DimensionSummary should have required fields."""
        from app.schemas.analysis import DimensionSummary

        schema = DimensionSummary(
            count=15,
            avg_exposure=0.68,
        )

        assert schema.count == 15
        assert schema.avg_exposure == 0.68

    def test_dimension_summary_validation(self):
        """DimensionSummary should validate count and avg_exposure."""
        from pydantic import ValidationError

        from app.schemas.analysis import DimensionSummary

        # Valid: zero values
        schema = DimensionSummary(count=0, avg_exposure=0.0)
        assert schema.count == 0
        assert schema.avg_exposure == 0.0

        # Valid: max exposure
        schema = DimensionSummary(count=100, avg_exposure=1.0)
        assert schema.avg_exposure == 1.0

        # Invalid: negative count
        with pytest.raises(ValidationError):
            DimensionSummary(count=-1, avg_exposure=0.5)

        # Invalid: exposure below 0.0
        with pytest.raises(ValidationError):
            DimensionSummary(count=10, avg_exposure=-0.1)

        # Invalid: exposure above 1.0
        with pytest.raises(ValidationError):
            DimensionSummary(count=10, avg_exposure=1.1)

    def test_trigger_analysis_response_fields(self):
        """TriggerAnalysisResponse should have status field."""
        from app.schemas.analysis import TriggerAnalysisResponse

        schema = TriggerAnalysisResponse(status="processing")
        assert schema.status == "processing"

    def test_all_dimensions_response(self):
        """AllDimensionsResponse should be a dict-like structure."""
        from app.schemas.analysis import AllDimensionsResponse, DimensionSummary

        summaries = {
            "ROLE": DimensionSummary(count=15, avg_exposure=0.68),
            "DEPARTMENT": DimensionSummary(count=8, avg_exposure=0.72),
        }
        schema = AllDimensionsResponse(root=summaries)

        assert schema.root["ROLE"].count == 15
        assert schema.root["DEPARTMENT"].avg_exposure == 0.72
