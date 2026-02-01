"""Tests for activities router."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers.activities import router
from app.services.activity_service import ActivityService, get_activity_service


@pytest.fixture
def mock_activity_service():
    """Mock activity service for testing."""
    service = MagicMock(spec=ActivityService)
    service.get_activities_by_session = AsyncMock()
    service.update_selection = AsyncMock()
    service.bulk_update_selection = AsyncMock()
    service.get_selection_count = AsyncMock()
    return service


@pytest.fixture
def app(mock_activity_service):
    """Create test FastAPI app with mocked dependencies."""
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_activity_service] = lambda: mock_activity_service
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


class TestGetActivities:
    """Tests for GET /discovery/sessions/{session_id}/activities."""

    def test_get_activities_returns_200(self, client, mock_activity_service):
        """Should return activities grouped by GWA for a session."""
        session_id = uuid4()
        dwa_id = str(uuid4())
        mock_activity_service.get_activities_by_session.return_value = [
            {
                "gwa_code": "4.A.1",
                "gwa_title": "Analyzing Data or Information",
                "dwas": [
                    {
                        "id": dwa_id,
                        "code": "4.A.1.a.1",
                        "title": "Analyze data",
                        "description": "Analyze data to identify trends",
                        "selected": True,
                        "gwa_code": "4.A.1",
                    }
                ],
            }
        ]

        response = client.get(f"/discovery/sessions/{session_id}/activities")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["gwa_code"] == "4.A.1"
        assert data[0]["gwa_title"] == "Analyzing Data or Information"
        assert len(data[0]["dwas"]) == 1
        assert data[0]["dwas"][0]["id"] == dwa_id
        assert data[0]["dwas"][0]["selected"] is True
        mock_activity_service.get_activities_by_session.assert_called_once_with(
            session_id=session_id, include_unselected=True
        )

    def test_get_activities_with_include_unselected_false(
        self, client, mock_activity_service
    ):
        """Should filter by include_unselected query parameter."""
        session_id = uuid4()
        mock_activity_service.get_activities_by_session.return_value = []

        response = client.get(
            f"/discovery/sessions/{session_id}/activities",
            params={"include_unselected": False},
        )

        assert response.status_code == 200
        mock_activity_service.get_activities_by_session.assert_called_once_with(
            session_id=session_id, include_unselected=False
        )

    def test_get_activities_empty_list(self, client, mock_activity_service):
        """Should return empty list when no activities exist."""
        session_id = uuid4()
        mock_activity_service.get_activities_by_session.return_value = []

        response = client.get(f"/discovery/sessions/{session_id}/activities")

        assert response.status_code == 200
        assert response.json() == []
        mock_activity_service.get_activities_by_session.assert_called_once_with(
            session_id=session_id, include_unselected=True
        )

    def test_get_activities_session_not_found_returns_404(
        self, client, mock_activity_service
    ):
        """Should return 404 if session not found."""
        session_id = uuid4()
        mock_activity_service.get_activities_by_session.return_value = None

        response = client.get(f"/discovery/sessions/{session_id}/activities")

        assert response.status_code == 404
        assert "session" in response.json()["detail"].lower()

    def test_get_activities_validates_uuid(self, client, mock_activity_service):
        """Should validate session ID is a valid UUID."""
        response = client.get("/discovery/sessions/not-a-uuid/activities")

        assert response.status_code == 422


class TestUpdateActivitySelection:
    """Tests for PUT /discovery/activities/{activity_id}."""

    def test_update_selection_returns_200(self, client, mock_activity_service):
        """Should update activity selection and return 200."""
        activity_id = uuid4()
        mock_activity_service.update_selection.return_value = {
            "id": str(activity_id),
            "code": "4.A.1.a.1",
            "title": "Analyze data",
            "description": "Analyze data to identify trends",
            "selected": True,
            "gwa_code": "4.A.1",
        }

        response = client.put(
            f"/discovery/activities/{activity_id}",
            json={"selected": True},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(activity_id)
        assert data["selected"] is True
        mock_activity_service.update_selection.assert_called_once_with(
            activity_id=activity_id, selected=True
        )

    def test_update_selection_deselect(self, client, mock_activity_service):
        """Should deselect an activity."""
        activity_id = uuid4()
        mock_activity_service.update_selection.return_value = {
            "id": str(activity_id),
            "code": "4.A.1.a.1",
            "title": "Analyze data",
            "description": None,
            "selected": False,
            "gwa_code": "4.A.1",
        }

        response = client.put(
            f"/discovery/activities/{activity_id}",
            json={"selected": False},
        )

        assert response.status_code == 200
        assert response.json()["selected"] is False
        mock_activity_service.update_selection.assert_called_once_with(
            activity_id=activity_id, selected=False
        )

    def test_update_selection_not_found_returns_404(
        self, client, mock_activity_service
    ):
        """Should return 404 if activity not found."""
        activity_id = uuid4()
        mock_activity_service.update_selection.return_value = None

        response = client.put(
            f"/discovery/activities/{activity_id}",
            json={"selected": True},
        )

        assert response.status_code == 404
        assert "activity" in response.json()["detail"].lower()

    def test_update_selection_validates_uuid(self, client, mock_activity_service):
        """Should validate activity ID is a valid UUID."""
        response = client.put(
            "/discovery/activities/not-a-uuid",
            json={"selected": True},
        )

        assert response.status_code == 422

    def test_update_selection_requires_selected_field(
        self, client, mock_activity_service
    ):
        """Should require selected field in request body."""
        activity_id = uuid4()

        response = client.put(
            f"/discovery/activities/{activity_id}",
            json={},
        )

        assert response.status_code == 422


class TestBulkSelectActivities:
    """Tests for POST /discovery/sessions/{session_id}/activities/select."""

    def test_bulk_select_returns_200(self, client, mock_activity_service):
        """Should bulk select activities and return count."""
        session_id = uuid4()
        activity_ids = [uuid4(), uuid4(), uuid4()]
        mock_activity_service.bulk_update_selection.return_value = {"updated_count": 3}

        response = client.post(
            f"/discovery/sessions/{session_id}/activities/select",
            json={"activity_ids": [str(id) for id in activity_ids], "selected": True},
        )

        assert response.status_code == 200
        assert response.json()["updated_count"] == 3
        mock_activity_service.bulk_update_selection.assert_called_once_with(
            session_id=session_id,
            activity_ids=activity_ids,
            selected=True,
        )

    def test_bulk_deselect_returns_200(self, client, mock_activity_service):
        """Should bulk deselect activities and return count."""
        session_id = uuid4()
        activity_ids = [uuid4(), uuid4()]
        mock_activity_service.bulk_update_selection.return_value = {"updated_count": 2}

        response = client.post(
            f"/discovery/sessions/{session_id}/activities/select",
            json={"activity_ids": [str(id) for id in activity_ids], "selected": False},
        )

        assert response.status_code == 200
        assert response.json()["updated_count"] == 2
        mock_activity_service.bulk_update_selection.assert_called_once_with(
            session_id=session_id,
            activity_ids=activity_ids,
            selected=False,
        )

    def test_bulk_select_empty_list(self, client, mock_activity_service):
        """Should handle empty activity list."""
        session_id = uuid4()
        mock_activity_service.bulk_update_selection.return_value = {"updated_count": 0}

        response = client.post(
            f"/discovery/sessions/{session_id}/activities/select",
            json={"activity_ids": [], "selected": True},
        )

        assert response.status_code == 200
        assert response.json()["updated_count"] == 0
        mock_activity_service.bulk_update_selection.assert_called_once_with(
            session_id=session_id,
            activity_ids=[],
            selected=True,
        )

    def test_bulk_select_session_not_found_returns_404(
        self, client, mock_activity_service
    ):
        """Should return 404 if session not found."""
        session_id = uuid4()
        mock_activity_service.bulk_update_selection.return_value = None

        response = client.post(
            f"/discovery/sessions/{session_id}/activities/select",
            json={"activity_ids": [str(uuid4())], "selected": True},
        )

        assert response.status_code == 404
        assert "session" in response.json()["detail"].lower()

    def test_bulk_select_validates_session_uuid(self, client, mock_activity_service):
        """Should validate session ID is a valid UUID."""
        response = client.post(
            "/discovery/sessions/not-a-uuid/activities/select",
            json={"activity_ids": [], "selected": True},
        )

        assert response.status_code == 422

    def test_bulk_select_validates_activity_uuids(self, client, mock_activity_service):
        """Should validate activity IDs are valid UUIDs."""
        session_id = uuid4()

        response = client.post(
            f"/discovery/sessions/{session_id}/activities/select",
            json={"activity_ids": ["not-a-uuid"], "selected": True},
        )

        assert response.status_code == 422

    def test_bulk_select_requires_activity_ids(self, client, mock_activity_service):
        """Should require activity_ids field in request body."""
        session_id = uuid4()

        response = client.post(
            f"/discovery/sessions/{session_id}/activities/select",
            json={"selected": True},
        )

        assert response.status_code == 422

    def test_bulk_select_requires_selected_field(self, client, mock_activity_service):
        """Should require selected field in request body."""
        session_id = uuid4()

        response = client.post(
            f"/discovery/sessions/{session_id}/activities/select",
            json={"activity_ids": []},
        )

        assert response.status_code == 422


class TestGetSelectionCount:
    """Tests for GET /discovery/sessions/{session_id}/activities/count."""

    def test_get_selection_count_returns_200(self, client, mock_activity_service):
        """Should return selection count statistics."""
        session_id = uuid4()
        mock_activity_service.get_selection_count.return_value = {
            "total": 100,
            "selected": 75,
            "unselected": 25,
        }

        response = client.get(f"/discovery/sessions/{session_id}/activities/count")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 100
        assert data["selected"] == 75
        assert data["unselected"] == 25
        mock_activity_service.get_selection_count.assert_called_once_with(
            session_id=session_id
        )

    def test_get_selection_count_zero_activities(self, client, mock_activity_service):
        """Should handle zero activities."""
        session_id = uuid4()
        mock_activity_service.get_selection_count.return_value = {
            "total": 0,
            "selected": 0,
            "unselected": 0,
        }

        response = client.get(f"/discovery/sessions/{session_id}/activities/count")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["selected"] == 0
        assert data["unselected"] == 0

    def test_get_selection_count_session_not_found_returns_404(
        self, client, mock_activity_service
    ):
        """Should return 404 if session not found."""
        session_id = uuid4()
        mock_activity_service.get_selection_count.return_value = None

        response = client.get(f"/discovery/sessions/{session_id}/activities/count")

        assert response.status_code == 404
        assert "session" in response.json()["detail"].lower()

    def test_get_selection_count_validates_uuid(self, client, mock_activity_service):
        """Should validate session ID is a valid UUID."""
        response = client.get("/discovery/sessions/not-a-uuid/activities/count")

        assert response.status_code == 422


class TestSchemas:
    """Tests for Pydantic schemas."""

    def test_dwa_response_fields(self):
        """DWAResponse should have required fields."""
        from app.schemas.activity import DWAResponse

        dwa_id = uuid4()
        schema = DWAResponse(
            id=dwa_id,
            code="4.A.1.a.1",
            title="Analyze data",
            description="Analyze data to identify trends",
            selected=True,
            gwa_code="4.A.1",
        )

        assert schema.id == dwa_id
        assert schema.code == "4.A.1.a.1"
        assert schema.title == "Analyze data"
        assert schema.description == "Analyze data to identify trends"
        assert schema.selected is True
        assert schema.gwa_code == "4.A.1"

    def test_dwa_response_optional_description(self):
        """DWAResponse should allow None for description."""
        from app.schemas.activity import DWAResponse

        schema = DWAResponse(
            id=uuid4(),
            code="4.A.1.a.1",
            title="Analyze data",
            description=None,
            selected=False,
            gwa_code="4.A.1",
        )

        assert schema.description is None

    def test_gwa_group_response_fields(self):
        """GWAGroupResponse should have required fields."""
        from app.schemas.activity import DWAResponse, GWAGroupResponse

        dwa = DWAResponse(
            id=uuid4(),
            code="4.A.1.a.1",
            title="Analyze data",
            description=None,
            selected=True,
            gwa_code="4.A.1",
        )
        schema = GWAGroupResponse(
            gwa_code="4.A.1",
            gwa_title="Analyzing Data or Information",
            dwas=[dwa],
        )

        assert schema.gwa_code == "4.A.1"
        assert schema.gwa_title == "Analyzing Data or Information"
        assert len(schema.dwas) == 1
        assert schema.dwas[0].code == "4.A.1.a.1"

    def test_gwa_group_response_empty_dwas(self):
        """GWAGroupResponse should allow empty dwas list."""
        from app.schemas.activity import GWAGroupResponse

        schema = GWAGroupResponse(
            gwa_code="4.A.1",
            gwa_title="Analyzing Data or Information",
            dwas=[],
        )

        assert schema.dwas == []

    def test_activity_selection_update_fields(self):
        """ActivitySelectionUpdate should have selected field."""
        from app.schemas.activity import ActivitySelectionUpdate

        schema = ActivitySelectionUpdate(selected=True)
        assert schema.selected is True

        schema2 = ActivitySelectionUpdate(selected=False)
        assert schema2.selected is False

    def test_bulk_selection_request_fields(self):
        """BulkSelectionRequest should have required fields."""
        from app.schemas.activity import BulkSelectionRequest

        activity_ids = [uuid4(), uuid4()]
        schema = BulkSelectionRequest(
            activity_ids=activity_ids,
            selected=True,
        )

        assert schema.activity_ids == activity_ids
        assert schema.selected is True

    def test_bulk_selection_request_empty_list(self):
        """BulkSelectionRequest should allow empty activity_ids list."""
        from app.schemas.activity import BulkSelectionRequest

        schema = BulkSelectionRequest(
            activity_ids=[],
            selected=False,
        )

        assert schema.activity_ids == []
        assert schema.selected is False

    def test_bulk_selection_response_fields(self):
        """BulkSelectionResponse should have updated_count field."""
        from app.schemas.activity import BulkSelectionResponse

        schema = BulkSelectionResponse(updated_count=5)
        assert schema.updated_count == 5

    def test_bulk_selection_response_zero_count(self):
        """BulkSelectionResponse should allow zero updated_count."""
        from app.schemas.activity import BulkSelectionResponse

        schema = BulkSelectionResponse(updated_count=0)
        assert schema.updated_count == 0

    def test_selection_count_response_fields(self):
        """SelectionCountResponse should have required fields."""
        from app.schemas.activity import SelectionCountResponse

        schema = SelectionCountResponse(
            total=100,
            selected=75,
            unselected=25,
        )

        assert schema.total == 100
        assert schema.selected == 75
        assert schema.unselected == 25

    def test_selection_count_response_zero_values(self):
        """SelectionCountResponse should allow zero values."""
        from app.schemas.activity import SelectionCountResponse

        schema = SelectionCountResponse(
            total=0,
            selected=0,
            unselected=0,
        )

        assert schema.total == 0
        assert schema.selected == 0
        assert schema.unselected == 0
