"""Tests for discovery handoff router."""
import pytest
from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers.handoff import router
from app.services.handoff_service import get_handoff_service
from pydantic import ValidationError

from app.schemas.handoff import (
    HandoffRequest,
    HandoffResponse,
    ValidationResult,
    HandoffStatus,
    HandoffError,
)
from app.schemas.analysis import PriorityTier


@pytest.fixture
def mock_handoff_service():
    """Mock handoff service for testing."""
    service = MagicMock()
    service.submit_to_intake = AsyncMock()
    service.validate_readiness = AsyncMock()
    service.get_status = AsyncMock()
    return service


@pytest.fixture
def app(mock_handoff_service):
    """Create test FastAPI app with mocked dependencies."""
    app = FastAPI()
    app.include_router(router)

    # Override dependency
    app.dependency_overrides[get_handoff_service] = lambda: mock_handoff_service

    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


class TestSubmitHandoff:
    """Tests for POST /discovery/sessions/{session_id}/handoff."""

    def test_submit_handoff_returns_201_with_intake_request_id(
        self, client, mock_handoff_service
    ):
        """Should return 201 with intake_request_id when submission succeeds."""
        session_id = uuid4()
        intake_request_id = uuid4()
        candidate_ids = [uuid4(), uuid4()]

        # Mock validation passes
        mock_handoff_service.validate_readiness.return_value = ValidationResult(
            is_ready=True,
            warnings=[],
            errors=[],
        )

        # Mock successful submission
        mock_handoff_service.submit_to_intake.return_value = HandoffResponse(
            intake_request_id=intake_request_id,
            status="submitted",
            candidates_count=2,
        )

        response = client.post(
            f"/discovery/sessions/{session_id}/handoff",
            json={
                "candidate_ids": [str(c) for c in candidate_ids],
                "notes": "Test handoff notes",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["intake_request_id"] == str(intake_request_id)
        assert data["status"] == "submitted"
        assert data["candidates_count"] == 2

    def test_submit_handoff_with_priority_tier_filter(
        self, client, mock_handoff_service
    ):
        """Should accept priority_tier filter for submission."""
        session_id = uuid4()
        intake_request_id = uuid4()

        # Mock validation passes
        mock_handoff_service.validate_readiness.return_value = ValidationResult(
            is_ready=True,
            warnings=[],
            errors=[],
        )

        # Mock successful submission
        mock_handoff_service.submit_to_intake.return_value = HandoffResponse(
            intake_request_id=intake_request_id,
            status="submitted",
            candidates_count=5,
        )

        response = client.post(
            f"/discovery/sessions/{session_id}/handoff",
            json={"priority_tier": "HIGH"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["intake_request_id"] == str(intake_request_id)
        assert data["status"] == "submitted"
        assert data["candidates_count"] == 5

        # Verify the service was called with priority_tier
        mock_handoff_service.submit_to_intake.assert_called_once()
        call_args = mock_handoff_service.submit_to_intake.call_args
        request_arg = call_args[0][1]  # Second positional arg is the request
        assert request_arg.priority_tier == PriorityTier.HIGH

    def test_submit_handoff_fails_with_400_when_not_ready(
        self, client, mock_handoff_service
    ):
        """Should return 400 when validation fails."""
        session_id = uuid4()
        candidate_ids = [uuid4()]

        # Mock validation fails
        mock_handoff_service.validate_readiness.return_value = ValidationResult(
            is_ready=False,
            warnings=["Some candidates have missing data"],
            errors=["No candidates selected for handoff"],
        )

        response = client.post(
            f"/discovery/sessions/{session_id}/handoff",
            json={"candidate_ids": [str(c) for c in candidate_ids]},
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "errors" in data["detail"]
        assert "No candidates selected for handoff" in data["detail"]["errors"]

        # Verify submit_to_intake was not called
        mock_handoff_service.submit_to_intake.assert_not_called()

    def test_submit_handoff_session_not_found_returns_404(
        self, client, mock_handoff_service
    ):
        """Should return 404 if session not found."""
        session_id = uuid4()

        # Mock validation returns None (session not found)
        mock_handoff_service.validate_readiness.return_value = None

        response = client.post(
            f"/discovery/sessions/{session_id}/handoff",
            json={"candidate_ids": [str(uuid4())]},
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_submit_handoff_validates_uuid(self, client, mock_handoff_service):
        """Should validate session ID is a valid UUID."""
        response = client.post(
            "/discovery/sessions/not-a-uuid/handoff",
            json={"candidate_ids": [str(uuid4())]},
        )

        assert response.status_code == 422

    def test_submit_handoff_rejects_both_candidate_ids_and_priority_tier(
        self, client, mock_handoff_service
    ):
        """Should return 422 when both candidate_ids and priority_tier are provided."""
        session_id = uuid4()

        response = client.post(
            f"/discovery/sessions/{session_id}/handoff",
            json={
                "candidate_ids": [str(uuid4()), str(uuid4())],
                "priority_tier": "HIGH",
            },
        )

        assert response.status_code == 422
        data = response.json()
        assert "candidate_ids" in str(data).lower() or "priority_tier" in str(data).lower()

    def test_submit_handoff_rejects_invalid_priority_tier(
        self, client, mock_handoff_service
    ):
        """Should return 422 when invalid priority_tier value is provided."""
        session_id = uuid4()

        response = client.post(
            f"/discovery/sessions/{session_id}/handoff",
            json={"priority_tier": "INVALID"},
        )

        assert response.status_code == 422
        data = response.json()
        assert "priority_tier" in str(data).lower()


class TestValidateHandoff:
    """Tests for POST /discovery/sessions/{session_id}/handoff/validate."""

    def test_validate_handoff_returns_200_with_is_ready_status(
        self, client, mock_handoff_service
    ):
        """Should return 200 with validation result."""
        session_id = uuid4()

        mock_handoff_service.validate_readiness.return_value = ValidationResult(
            is_ready=True,
            warnings=["Optional: Add more context notes"],
            errors=[],
        )

        response = client.post(f"/discovery/sessions/{session_id}/handoff/validate")

        assert response.status_code == 200
        data = response.json()
        assert data["is_ready"] is True
        assert data["warnings"] == ["Optional: Add more context notes"]
        assert data["errors"] == []

    def test_validate_handoff_returns_not_ready_status(
        self, client, mock_handoff_service
    ):
        """Should return is_ready=False when validation fails."""
        session_id = uuid4()

        mock_handoff_service.validate_readiness.return_value = ValidationResult(
            is_ready=False,
            warnings=[],
            errors=["Session analysis incomplete", "No candidates selected"],
        )

        response = client.post(f"/discovery/sessions/{session_id}/handoff/validate")

        assert response.status_code == 200
        data = response.json()
        assert data["is_ready"] is False
        assert len(data["errors"]) == 2

    def test_validate_handoff_session_not_found_returns_404(
        self, client, mock_handoff_service
    ):
        """Should return 404 if session not found."""
        session_id = uuid4()

        mock_handoff_service.validate_readiness.return_value = None

        response = client.post(f"/discovery/sessions/{session_id}/handoff/validate")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_validate_handoff_validates_uuid(self, client, mock_handoff_service):
        """Should validate session ID is a valid UUID."""
        response = client.post("/discovery/sessions/not-a-uuid/handoff/validate")

        assert response.status_code == 422


class TestGetHandoffStatus:
    """Tests for GET /discovery/sessions/{session_id}/handoff."""

    def test_get_status_returns_200_with_handoff_status(
        self, client, mock_handoff_service
    ):
        """Should return 200 with handoff status."""
        session_id = uuid4()
        intake_request_id = uuid4()
        handed_off_at = datetime.now(UTC)

        mock_handoff_service.get_status.return_value = HandoffStatus(
            session_id=session_id,
            handed_off=True,
            intake_request_id=intake_request_id,
            handed_off_at=handed_off_at,
        )

        response = client.get(f"/discovery/sessions/{session_id}/handoff")

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == str(session_id)
        assert data["handed_off"] is True
        assert data["intake_request_id"] == str(intake_request_id)
        assert data["handed_off_at"] is not None

    def test_get_status_returns_not_handed_off(self, client, mock_handoff_service):
        """Should return status with handed_off=False when not yet handed off."""
        session_id = uuid4()

        mock_handoff_service.get_status.return_value = HandoffStatus(
            session_id=session_id,
            handed_off=False,
            intake_request_id=None,
            handed_off_at=None,
        )

        response = client.get(f"/discovery/sessions/{session_id}/handoff")

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == str(session_id)
        assert data["handed_off"] is False
        assert data["intake_request_id"] is None
        assert data["handed_off_at"] is None

    def test_get_status_session_not_found_returns_404(
        self, client, mock_handoff_service
    ):
        """Should return 404 if session not found."""
        session_id = uuid4()

        mock_handoff_service.get_status.return_value = None

        response = client.get(f"/discovery/sessions/{session_id}/handoff")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_status_validates_uuid(self, client, mock_handoff_service):
        """Should validate session ID is a valid UUID."""
        response = client.get("/discovery/sessions/not-a-uuid/handoff")

        assert response.status_code == 422


class TestHandoffSchemas:
    """Tests for handoff Pydantic schemas."""

    def test_handoff_request_with_candidate_ids(self):
        """HandoffRequest should accept candidate_ids."""
        candidate_ids = [uuid4(), uuid4()]
        request = HandoffRequest(
            candidate_ids=candidate_ids,
            notes="Test notes",
        )
        assert request.candidate_ids == candidate_ids
        assert request.notes == "Test notes"
        assert request.priority_tier is None

    def test_handoff_request_with_priority_tier(self):
        """HandoffRequest should accept priority_tier."""
        request = HandoffRequest(priority_tier=PriorityTier.HIGH)
        assert request.priority_tier == PriorityTier.HIGH
        assert request.candidate_ids is None
        assert request.notes is None

    def test_handoff_request_with_priority_tier_string(self):
        """HandoffRequest should accept priority_tier as string and convert to enum."""
        request = HandoffRequest(priority_tier="HIGH")
        assert request.priority_tier == PriorityTier.HIGH

    def test_handoff_request_rejects_both_candidate_ids_and_priority_tier(self):
        """HandoffRequest should reject when both candidate_ids and priority_tier are provided."""
        with pytest.raises(ValidationError) as exc_info:
            HandoffRequest(
                candidate_ids=[uuid4(), uuid4()],
                priority_tier=PriorityTier.HIGH,
            )
        assert "Provide either candidate_ids or priority_tier, not both" in str(exc_info.value)

    def test_handoff_request_invalid_priority_tier(self):
        """HandoffRequest should reject invalid priority_tier values."""
        with pytest.raises(ValidationError) as exc_info:
            HandoffRequest(priority_tier="INVALID")
        assert "priority_tier" in str(exc_info.value).lower()

    def test_handoff_response_has_required_fields(self):
        """HandoffResponse should have all required fields."""
        intake_request_id = uuid4()
        response = HandoffResponse(
            intake_request_id=intake_request_id,
            status="submitted",
            candidates_count=3,
        )
        assert response.intake_request_id == intake_request_id
        assert response.status == "submitted"
        assert response.candidates_count == 3

    def test_validation_result_defaults(self):
        """ValidationResult should have default empty lists."""
        result = ValidationResult(is_ready=True)
        assert result.is_ready is True
        assert result.warnings == []
        assert result.errors == []

    def test_handoff_status_with_all_fields(self):
        """HandoffStatus should accept all fields."""
        session_id = uuid4()
        intake_request_id = uuid4()
        handed_off_at = datetime.now(UTC)

        status = HandoffStatus(
            session_id=session_id,
            handed_off=True,
            intake_request_id=intake_request_id,
            handed_off_at=handed_off_at,
        )
        assert status.session_id == session_id
        assert status.handed_off is True
        assert status.intake_request_id == intake_request_id
        assert status.handed_off_at == handed_off_at

    def test_handoff_status_with_optional_fields_none(self):
        """HandoffStatus should accept None for optional fields."""
        session_id = uuid4()
        status = HandoffStatus(
            session_id=session_id,
            handed_off=False,
        )
        assert status.session_id == session_id
        assert status.handed_off is False
        assert status.intake_request_id is None
        assert status.handed_off_at is None

    def test_handoff_error_has_required_fields(self):
        """HandoffError should have detail and errors."""
        error = HandoffError(
            detail="Validation failed",
            errors=["Error 1", "Error 2"],
        )
        assert error.detail == "Validation failed"
        assert error.errors == ["Error 1", "Error 2"]
