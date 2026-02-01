"""Tests for roadmap router."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers.roadmap import router
from app.services.roadmap_service import (
    RoadmapService,
    get_roadmap_service,
)
from app.schemas.roadmap import (
    RoadmapPhase,
    EstimatedEffort,
)


@pytest.fixture
def mock_roadmap_service():
    """Mock roadmap service for testing."""
    service = MagicMock(spec=RoadmapService)
    service.get_roadmap = AsyncMock()
    service.update_phase = AsyncMock()
    service.reorder = AsyncMock()
    service.bulk_update = AsyncMock()
    return service


@pytest.fixture
def app(mock_roadmap_service):
    """Create test FastAPI app with mocked dependencies."""
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_roadmap_service] = lambda: mock_roadmap_service
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


class TestGetRoadmap:
    """Tests for GET /discovery/sessions/{session_id}/roadmap."""

    def test_get_roadmap_returns_200_with_items(self, client, mock_roadmap_service):
        """Should return roadmap items for a session."""
        session_id = uuid4()
        item_id = uuid4()
        mock_roadmap_service.get_roadmap.return_value = [
            {
                "id": str(item_id),
                "role_name": "Data Analyst",
                "priority_score": 0.85,
                "priority_tier": "HIGH",
                "phase": "NOW",
                "estimated_effort": "medium",
                "order": 1,
            }
        ]

        response = client.get(f"/discovery/sessions/{session_id}/roadmap")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == str(item_id)
        assert data["items"][0]["role_name"] == "Data Analyst"
        assert data["items"][0]["priority_score"] == 0.85
        assert data["items"][0]["priority_tier"] == "HIGH"
        assert data["items"][0]["phase"] == "NOW"
        assert data["items"][0]["estimated_effort"] == "medium"
        assert data["items"][0]["order"] == 1
        mock_roadmap_service.get_roadmap.assert_called_once_with(
            session_id=session_id,
            phase=None,
        )

    def test_get_roadmap_with_phase_filter(self, client, mock_roadmap_service):
        """Should filter roadmap items by phase."""
        session_id = uuid4()
        item_id = uuid4()
        mock_roadmap_service.get_roadmap.return_value = [
            {
                "id": str(item_id),
                "role_name": "Software Engineer",
                "priority_score": 0.70,
                "priority_tier": "MEDIUM",
                "phase": "NEXT",
                "estimated_effort": "high",
                "order": 1,
            }
        ]

        response = client.get(
            f"/discovery/sessions/{session_id}/roadmap",
            params={"phase": "NEXT"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["items"][0]["phase"] == "NEXT"
        mock_roadmap_service.get_roadmap.assert_called_once_with(
            session_id=session_id,
            phase=RoadmapPhase.NEXT,
        )

    def test_get_roadmap_all_phases(self, client, mock_roadmap_service):
        """Should accept all valid phase filter values."""
        session_id = uuid4()
        mock_roadmap_service.get_roadmap.return_value = []

        for phase in ["NOW", "NEXT", "LATER"]:
            response = client.get(
                f"/discovery/sessions/{session_id}/roadmap",
                params={"phase": phase},
            )
            assert response.status_code == 200

    def test_get_roadmap_empty_list(self, client, mock_roadmap_service):
        """Should return empty items list when no roadmap items exist."""
        session_id = uuid4()
        mock_roadmap_service.get_roadmap.return_value = []

        response = client.get(f"/discovery/sessions/{session_id}/roadmap")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []

    def test_get_roadmap_session_not_found_returns_404(
        self, client, mock_roadmap_service
    ):
        """Should return 404 if session not found."""
        session_id = uuid4()
        mock_roadmap_service.get_roadmap.return_value = None

        response = client.get(f"/discovery/sessions/{session_id}/roadmap")

        assert response.status_code == 404
        assert "session" in response.json()["detail"].lower()

    def test_get_roadmap_validates_uuid(self, client, mock_roadmap_service):
        """Should validate session ID is a valid UUID."""
        response = client.get("/discovery/sessions/not-a-uuid/roadmap")

        assert response.status_code == 422

    def test_get_roadmap_invalid_phase_returns_422(self, client, mock_roadmap_service):
        """Should return 422 for invalid phase filter."""
        session_id = uuid4()

        response = client.get(
            f"/discovery/sessions/{session_id}/roadmap",
            params={"phase": "INVALID_PHASE"},
        )

        assert response.status_code == 422


class TestUpdatePhase:
    """Tests for PUT /discovery/roadmap/{item_id}."""

    def test_update_phase_returns_200(self, client, mock_roadmap_service):
        """Should update roadmap item phase and return updated item."""
        item_id = uuid4()
        mock_roadmap_service.update_phase.return_value = {
            "id": str(item_id),
            "role_name": "Data Analyst",
            "priority_score": 0.85,
            "priority_tier": "HIGH",
            "phase": "NEXT",
            "estimated_effort": "medium",
            "order": 2,
        }

        response = client.put(
            f"/discovery/roadmap/{item_id}",
            json={"phase": "NEXT"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(item_id)
        assert data["phase"] == "NEXT"
        mock_roadmap_service.update_phase.assert_called_once_with(
            item_id=item_id,
            phase=RoadmapPhase.NEXT,
        )

    def test_update_phase_all_phases(self, client, mock_roadmap_service):
        """Should accept all valid phase values."""
        item_id = uuid4()

        for phase in ["NOW", "NEXT", "LATER"]:
            mock_roadmap_service.update_phase.return_value = {
                "id": str(item_id),
                "role_name": "Test Role",
                "priority_score": 0.5,
                "priority_tier": "MEDIUM",
                "phase": phase,
                "estimated_effort": "low",
                "order": 1,
            }

            response = client.put(
                f"/discovery/roadmap/{item_id}",
                json={"phase": phase},
            )
            assert response.status_code == 200
            assert response.json()["phase"] == phase

    def test_update_phase_item_not_found_returns_404(
        self, client, mock_roadmap_service
    ):
        """Should return 404 if item not found."""
        item_id = uuid4()
        mock_roadmap_service.update_phase.return_value = None

        response = client.put(
            f"/discovery/roadmap/{item_id}",
            json={"phase": "NEXT"},
        )

        assert response.status_code == 404
        assert "item" in response.json()["detail"].lower()

    def test_update_phase_validates_uuid(self, client, mock_roadmap_service):
        """Should validate item ID is a valid UUID."""
        response = client.put(
            "/discovery/roadmap/not-a-uuid",
            json={"phase": "NOW"},
        )

        assert response.status_code == 422

    def test_update_phase_invalid_phase_returns_422(self, client, mock_roadmap_service):
        """Should return 422 for invalid phase value."""
        item_id = uuid4()

        response = client.put(
            f"/discovery/roadmap/{item_id}",
            json={"phase": "INVALID_PHASE"},
        )

        assert response.status_code == 422

    def test_update_phase_missing_phase_returns_422(self, client, mock_roadmap_service):
        """Should return 422 if phase is missing from request body."""
        item_id = uuid4()

        response = client.put(
            f"/discovery/roadmap/{item_id}",
            json={},
        )

        assert response.status_code == 422


class TestReorderRoadmap:
    """Tests for POST /discovery/sessions/{session_id}/roadmap/reorder."""

    def test_reorder_returns_200_success(self, client, mock_roadmap_service):
        """Should reorder items and return success."""
        session_id = uuid4()
        item_ids = [uuid4(), uuid4(), uuid4()]
        mock_roadmap_service.reorder.return_value = True

        response = client.post(
            f"/discovery/sessions/{session_id}/roadmap/reorder",
            json={"item_ids": [str(id) for id in item_ids]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        mock_roadmap_service.reorder.assert_called_once_with(
            session_id=session_id,
            item_ids=item_ids,
        )

    def test_reorder_session_not_found_returns_404(
        self, client, mock_roadmap_service
    ):
        """Should return 404 if session not found."""
        session_id = uuid4()
        mock_roadmap_service.reorder.return_value = None

        response = client.post(
            f"/discovery/sessions/{session_id}/roadmap/reorder",
            json={"item_ids": [str(uuid4())]},
        )

        assert response.status_code == 404
        assert "session" in response.json()["detail"].lower()

    def test_reorder_validates_session_uuid(self, client, mock_roadmap_service):
        """Should validate session ID is a valid UUID."""
        response = client.post(
            "/discovery/sessions/not-a-uuid/roadmap/reorder",
            json={"item_ids": [str(uuid4())]},
        )

        assert response.status_code == 422

    def test_reorder_validates_item_uuids(self, client, mock_roadmap_service):
        """Should validate item IDs are valid UUIDs."""
        session_id = uuid4()

        response = client.post(
            f"/discovery/sessions/{session_id}/roadmap/reorder",
            json={"item_ids": ["not-a-uuid"]},
        )

        assert response.status_code == 422

    def test_reorder_empty_list(self, client, mock_roadmap_service):
        """Should accept empty item_ids list."""
        session_id = uuid4()
        mock_roadmap_service.reorder.return_value = True

        response = client.post(
            f"/discovery/sessions/{session_id}/roadmap/reorder",
            json={"item_ids": []},
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_reorder_missing_item_ids_returns_422(self, client, mock_roadmap_service):
        """Should return 422 if item_ids is missing."""
        session_id = uuid4()

        response = client.post(
            f"/discovery/sessions/{session_id}/roadmap/reorder",
            json={},
        )

        assert response.status_code == 422


class TestBulkUpdatePhases:
    """Tests for POST /discovery/sessions/{session_id}/roadmap/bulk-update."""

    def test_bulk_update_returns_200_with_count(self, client, mock_roadmap_service):
        """Should bulk update phases and return count."""
        session_id = uuid4()
        item_id1 = uuid4()
        item_id2 = uuid4()
        mock_roadmap_service.bulk_update.return_value = 2

        response = client.post(
            f"/discovery/sessions/{session_id}/roadmap/bulk-update",
            json={
                "updates": [
                    {"id": str(item_id1), "phase": "NOW"},
                    {"id": str(item_id2), "phase": "NEXT"},
                ]
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["updated_count"] == 2

    def test_bulk_update_session_not_found_returns_404(
        self, client, mock_roadmap_service
    ):
        """Should return 404 if session not found."""
        session_id = uuid4()
        mock_roadmap_service.bulk_update.return_value = None

        response = client.post(
            f"/discovery/sessions/{session_id}/roadmap/bulk-update",
            json={
                "updates": [
                    {"id": str(uuid4()), "phase": "NOW"},
                ]
            },
        )

        assert response.status_code == 404
        assert "session" in response.json()["detail"].lower()

    def test_bulk_update_validates_session_uuid(self, client, mock_roadmap_service):
        """Should validate session ID is a valid UUID."""
        response = client.post(
            "/discovery/sessions/not-a-uuid/roadmap/bulk-update",
            json={"updates": []},
        )

        assert response.status_code == 422

    def test_bulk_update_validates_item_uuids(self, client, mock_roadmap_service):
        """Should validate item IDs are valid UUIDs."""
        session_id = uuid4()

        response = client.post(
            f"/discovery/sessions/{session_id}/roadmap/bulk-update",
            json={
                "updates": [
                    {"id": "not-a-uuid", "phase": "NOW"},
                ]
            },
        )

        assert response.status_code == 422

    def test_bulk_update_validates_phases(self, client, mock_roadmap_service):
        """Should validate phase values."""
        session_id = uuid4()

        response = client.post(
            f"/discovery/sessions/{session_id}/roadmap/bulk-update",
            json={
                "updates": [
                    {"id": str(uuid4()), "phase": "INVALID"},
                ]
            },
        )

        assert response.status_code == 422

    def test_bulk_update_empty_updates(self, client, mock_roadmap_service):
        """Should accept empty updates list."""
        session_id = uuid4()
        mock_roadmap_service.bulk_update.return_value = 0

        response = client.post(
            f"/discovery/sessions/{session_id}/roadmap/bulk-update",
            json={"updates": []},
        )

        assert response.status_code == 200
        assert response.json()["updated_count"] == 0

    def test_bulk_update_missing_updates_returns_422(
        self, client, mock_roadmap_service
    ):
        """Should return 422 if updates is missing."""
        session_id = uuid4()

        response = client.post(
            f"/discovery/sessions/{session_id}/roadmap/bulk-update",
            json={},
        )

        assert response.status_code == 422


class TestSchemas:
    """Tests for Pydantic schemas."""

    def test_roadmap_phase_enum_values(self):
        """RoadmapPhase should have all required values."""
        from app.schemas.roadmap import RoadmapPhase

        assert RoadmapPhase.NOW.value == "NOW"
        assert RoadmapPhase.NEXT.value == "NEXT"
        assert RoadmapPhase.LATER.value == "LATER"

    def test_estimated_effort_enum_values(self):
        """EstimatedEffort should have all required values."""
        from app.schemas.roadmap import EstimatedEffort

        assert EstimatedEffort.LOW.value == "low"
        assert EstimatedEffort.MEDIUM.value == "medium"
        assert EstimatedEffort.HIGH.value == "high"

    def test_roadmap_item_fields(self):
        """RoadmapItem should have required fields."""
        from app.schemas.roadmap import (
            RoadmapItem,
            RoadmapPhase,
            EstimatedEffort,
        )

        item_id = uuid4()
        schema = RoadmapItem(
            id=item_id,
            role_name="Data Analyst",
            priority_score=0.85,
            priority_tier="HIGH",
            phase=RoadmapPhase.NOW,
            estimated_effort=EstimatedEffort.MEDIUM,
            order=1,
        )

        assert schema.id == item_id
        assert schema.role_name == "Data Analyst"
        assert schema.priority_score == 0.85
        assert schema.priority_tier == "HIGH"
        assert schema.phase == RoadmapPhase.NOW
        assert schema.estimated_effort == EstimatedEffort.MEDIUM
        assert schema.order == 1

    def test_roadmap_item_optional_order(self):
        """RoadmapItem should allow None for order."""
        from app.schemas.roadmap import (
            RoadmapItem,
            RoadmapPhase,
            EstimatedEffort,
        )

        schema = RoadmapItem(
            id=uuid4(),
            role_name="Test Role",
            priority_score=0.5,
            priority_tier="MEDIUM",
            phase=RoadmapPhase.LATER,
            estimated_effort=EstimatedEffort.LOW,
        )

        assert schema.order is None

    def test_roadmap_item_score_validation(self):
        """RoadmapItem should validate score ranges (0.0-1.0)."""
        from pydantic import ValidationError

        from app.schemas.roadmap import (
            RoadmapItem,
            RoadmapPhase,
            EstimatedEffort,
        )

        # Valid boundary values
        schema = RoadmapItem(
            id=uuid4(),
            role_name="Test",
            priority_score=0.0,
            priority_tier="LOW",
            phase=RoadmapPhase.LATER,
            estimated_effort=EstimatedEffort.LOW,
        )
        assert schema.priority_score == 0.0

        schema = RoadmapItem(
            id=uuid4(),
            role_name="Test",
            priority_score=1.0,
            priority_tier="HIGH",
            phase=RoadmapPhase.NOW,
            estimated_effort=EstimatedEffort.HIGH,
        )
        assert schema.priority_score == 1.0

        # Invalid: below 0.0
        with pytest.raises(ValidationError):
            RoadmapItem(
                id=uuid4(),
                role_name="Test",
                priority_score=-0.1,
                priority_tier="LOW",
                phase=RoadmapPhase.LATER,
                estimated_effort=EstimatedEffort.LOW,
            )

        # Invalid: above 1.0
        with pytest.raises(ValidationError):
            RoadmapItem(
                id=uuid4(),
                role_name="Test",
                priority_score=1.1,
                priority_tier="HIGH",
                phase=RoadmapPhase.NOW,
                estimated_effort=EstimatedEffort.HIGH,
            )

    def test_phase_update_fields(self):
        """PhaseUpdate should have phase field."""
        from app.schemas.roadmap import PhaseUpdate, RoadmapPhase

        schema = PhaseUpdate(phase=RoadmapPhase.NEXT)
        assert schema.phase == RoadmapPhase.NEXT

    def test_reorder_request_fields(self):
        """ReorderRequest should have item_ids field."""
        from app.schemas.roadmap import ReorderRequest

        item_ids = [uuid4(), uuid4()]
        schema = ReorderRequest(item_ids=item_ids)
        assert schema.item_ids == item_ids

    def test_reorder_response_fields(self):
        """ReorderResponse should have success field."""
        from app.schemas.roadmap import ReorderResponse

        schema = ReorderResponse(success=True)
        assert schema.success is True

    def test_bulk_phase_update_fields(self):
        """BulkPhaseUpdate should have id and phase fields."""
        from app.schemas.roadmap import BulkPhaseUpdate, RoadmapPhase

        item_id = uuid4()
        schema = BulkPhaseUpdate(id=item_id, phase=RoadmapPhase.NOW)
        assert schema.id == item_id
        assert schema.phase == RoadmapPhase.NOW

    def test_bulk_update_request_fields(self):
        """BulkUpdateRequest should have updates field."""
        from app.schemas.roadmap import (
            BulkUpdateRequest,
            BulkPhaseUpdate,
            RoadmapPhase,
        )

        updates = [
            BulkPhaseUpdate(id=uuid4(), phase=RoadmapPhase.NOW),
            BulkPhaseUpdate(id=uuid4(), phase=RoadmapPhase.NEXT),
        ]
        schema = BulkUpdateRequest(updates=updates)
        assert len(schema.updates) == 2

    def test_bulk_update_response_fields(self):
        """BulkUpdateResponse should have updated_count field."""
        from app.schemas.roadmap import BulkUpdateResponse

        schema = BulkUpdateResponse(updated_count=5)
        assert schema.updated_count == 5

    def test_bulk_update_response_validation(self):
        """BulkUpdateResponse should validate count is non-negative."""
        from pydantic import ValidationError

        from app.schemas.roadmap import BulkUpdateResponse

        # Valid: zero
        schema = BulkUpdateResponse(updated_count=0)
        assert schema.updated_count == 0

        # Invalid: negative
        with pytest.raises(ValidationError):
            BulkUpdateResponse(updated_count=-1)

    def test_roadmap_items_response_fields(self):
        """RoadmapItemsResponse should have items field."""
        from app.schemas.roadmap import (
            RoadmapItemsResponse,
            RoadmapItem,
            RoadmapPhase,
            EstimatedEffort,
        )

        items = [
            RoadmapItem(
                id=uuid4(),
                role_name="Test Role",
                priority_score=0.5,
                priority_tier="MEDIUM",
                phase=RoadmapPhase.NEXT,
                estimated_effort=EstimatedEffort.MEDIUM,
            )
        ]
        schema = RoadmapItemsResponse(items=items)
        assert len(schema.items) == 1
        assert schema.items[0].role_name == "Test Role"
