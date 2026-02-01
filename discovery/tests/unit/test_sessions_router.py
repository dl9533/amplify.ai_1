"""Tests for discovery session router."""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers.sessions import router, get_session_service
from app.schemas.session import SessionCreate, SessionResponse, SessionList, StepUpdate


@pytest.fixture
def mock_session_service():
    """Mock session service for testing."""
    service = MagicMock()
    service.create = AsyncMock()
    service.get_by_id = AsyncMock()
    service.list_for_user = AsyncMock()
    service.update_step = AsyncMock()
    service.delete = AsyncMock()
    return service


@pytest.fixture
def app(mock_session_service):
    """Create test FastAPI app with mocked dependencies."""
    app = FastAPI()
    app.include_router(router)

    # Override dependency
    app.dependency_overrides[get_session_service] = lambda: mock_session_service

    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


class TestCreateSession:
    """Tests for POST /discovery/sessions."""

    def test_create_session_returns_201(self, client, mock_session_service):
        """Should create session and return 201."""
        org_id = uuid4()
        session_id = uuid4()
        now = datetime.now(timezone.utc)

        mock_session_service.create.return_value = {
            "id": str(session_id),
            "status": "draft",
            "current_step": 1,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        response = client.post(
            "/discovery/sessions",
            json={"organization_id": str(org_id)},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == str(session_id)
        assert data["status"] == "draft"
        assert data["current_step"] == 1
        mock_session_service.create.assert_called_once()

    def test_create_session_validates_org_id(self, client, mock_session_service):
        """Should validate organization_id is a valid UUID."""
        response = client.post(
            "/discovery/sessions",
            json={"organization_id": "not-a-uuid"},
        )

        assert response.status_code == 422


class TestGetSession:
    """Tests for GET /discovery/sessions/{id}."""

    def test_get_session_returns_200(self, client, mock_session_service):
        """Should return session details."""
        session_id = uuid4()
        now = datetime.now(timezone.utc)

        mock_session_service.get_by_id.return_value = {
            "id": str(session_id),
            "status": "in_progress",
            "current_step": 2,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        response = client.get(f"/discovery/sessions/{session_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(session_id)
        assert data["status"] == "in_progress"
        assert data["current_step"] == 2
        mock_session_service.get_by_id.assert_called_once()

    def test_get_session_not_found_returns_404(self, client, mock_session_service):
        """Should return 404 if session not found."""
        session_id = uuid4()
        mock_session_service.get_by_id.return_value = None

        response = client.get(f"/discovery/sessions/{session_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_session_validates_uuid(self, client, mock_session_service):
        """Should validate session ID is a valid UUID."""
        response = client.get("/discovery/sessions/not-a-uuid")

        assert response.status_code == 422


class TestListSessions:
    """Tests for GET /discovery/sessions."""

    def test_list_sessions_returns_paginated(self, client, mock_session_service):
        """Should return paginated list."""
        session_id = uuid4()
        now = datetime.now(timezone.utc)

        mock_session_service.list_for_user.return_value = {
            "items": [
                {
                    "id": str(session_id),
                    "status": "draft",
                    "current_step": 1,
                    "created_at": now.isoformat(),
                    "updated_at": now.isoformat(),
                }
            ],
            "total": 1,
            "page": 1,
            "per_page": 20,
        }

        response = client.get("/discovery/sessions")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) == 1
        assert data["total"] == 1
        assert data["page"] == 1
        assert data["per_page"] == 20

    def test_list_sessions_accepts_pagination_params(self, client, mock_session_service):
        """Should accept page and per_page parameters."""
        mock_session_service.list_for_user.return_value = {
            "items": [],
            "total": 0,
            "page": 2,
            "per_page": 10,
        }

        response = client.get("/discovery/sessions?page=2&per_page=10")

        assert response.status_code == 200
        mock_session_service.list_for_user.assert_called_once()
        # Verify pagination params were passed
        call_kwargs = mock_session_service.list_for_user.call_args
        assert call_kwargs.kwargs.get("page") == 2
        assert call_kwargs.kwargs.get("per_page") == 10

    def test_list_sessions_empty_returns_empty_list(self, client, mock_session_service):
        """Should return empty list when no sessions exist."""
        mock_session_service.list_for_user.return_value = {
            "items": [],
            "total": 0,
            "page": 1,
            "per_page": 20,
        }

        response = client.get("/discovery/sessions")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0


class TestUpdateStep:
    """Tests for PATCH /discovery/sessions/{id}/step."""

    def test_update_step_returns_200(self, client, mock_session_service):
        """Should update step and return 200."""
        session_id = uuid4()
        now = datetime.now(timezone.utc)

        mock_session_service.update_step.return_value = {
            "id": str(session_id),
            "status": "in_progress",
            "current_step": 3,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        response = client.patch(
            f"/discovery/sessions/{session_id}/step",
            json={"step": 3},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["current_step"] == 3
        mock_session_service.update_step.assert_called_once()

    def test_update_step_not_found_returns_404(self, client, mock_session_service):
        """Should return 404 if session not found."""
        session_id = uuid4()
        mock_session_service.update_step.return_value = None

        response = client.patch(
            f"/discovery/sessions/{session_id}/step",
            json={"step": 3},
        )

        assert response.status_code == 404

    def test_update_step_validates_step_is_positive(self, client, mock_session_service):
        """Should validate step is a positive integer."""
        session_id = uuid4()

        response = client.patch(
            f"/discovery/sessions/{session_id}/step",
            json={"step": -1},
        )

        assert response.status_code == 422


class TestDeleteSession:
    """Tests for DELETE /discovery/sessions/{id}."""

    def test_delete_session_returns_204(self, client, mock_session_service):
        """Should delete session and return 204."""
        session_id = uuid4()
        mock_session_service.delete.return_value = True

        response = client.delete(f"/discovery/sessions/{session_id}")

        assert response.status_code == 204
        mock_session_service.delete.assert_called_once()

    def test_delete_session_not_found_returns_404(self, client, mock_session_service):
        """Should return 404 if session not found."""
        session_id = uuid4()
        mock_session_service.delete.return_value = False

        response = client.delete(f"/discovery/sessions/{session_id}")

        assert response.status_code == 404

    def test_delete_session_validates_uuid(self, client, mock_session_service):
        """Should validate session ID is a valid UUID."""
        response = client.delete("/discovery/sessions/not-a-uuid")

        assert response.status_code == 422


class TestSchemas:
    """Tests for Pydantic schemas."""

    def test_session_create_requires_organization_id(self):
        """SessionCreate should require organization_id."""
        org_id = uuid4()
        schema = SessionCreate(organization_id=org_id)
        assert schema.organization_id == org_id

    def test_session_response_has_required_fields(self):
        """SessionResponse should have all required fields."""
        session_id = uuid4()
        now = datetime.now(timezone.utc)

        schema = SessionResponse(
            id=session_id,
            status="draft",
            current_step=1,
            created_at=now,
            updated_at=now,
        )

        assert schema.id == session_id
        assert schema.status == "draft"
        assert schema.current_step == 1
        assert schema.created_at == now
        assert schema.updated_at == now

    def test_session_list_has_pagination_fields(self):
        """SessionList should have pagination fields."""
        session_id = uuid4()
        now = datetime.now(timezone.utc)

        schema = SessionList(
            items=[
                SessionResponse(
                    id=session_id,
                    status="draft",
                    current_step=1,
                    created_at=now,
                    updated_at=now,
                )
            ],
            total=1,
            page=1,
            per_page=20,
        )

        assert len(schema.items) == 1
        assert schema.total == 1
        assert schema.page == 1
        assert schema.per_page == 20

    def test_step_update_requires_step(self):
        """StepUpdate should require step field."""
        schema = StepUpdate(step=3)
        assert schema.step == 3

    def test_step_update_validates_positive_step(self):
        """StepUpdate should validate step is positive."""
        with pytest.raises(ValueError):
            StepUpdate(step=0)

        with pytest.raises(ValueError):
            StepUpdate(step=-1)
