"""Tests for role mappings router."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers.role_mappings import router, get_role_mapping_service, get_onet_service


@pytest.fixture
def mock_role_mapping_service():
    """Mock role mapping service for testing."""
    service = MagicMock()
    service.get_by_session_id = AsyncMock()
    service.update = AsyncMock()
    service.bulk_confirm = AsyncMock()
    return service


@pytest.fixture
def mock_onet_service():
    """Mock O*NET service for testing."""
    service = MagicMock()
    service.search = AsyncMock()
    service.get_occupation = AsyncMock()
    return service


@pytest.fixture
def app(mock_role_mapping_service, mock_onet_service):
    """Create test FastAPI app with mocked dependencies."""
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_role_mapping_service] = lambda: mock_role_mapping_service
    app.dependency_overrides[get_onet_service] = lambda: mock_onet_service
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


class TestGetRoleMappings:
    """Tests for GET /discovery/sessions/{session_id}/role-mappings."""

    def test_get_role_mappings_returns_200(self, client, mock_role_mapping_service):
        """Should return role mappings for a session."""
        session_id = str(uuid4())
        mapping_id = str(uuid4())
        mock_role_mapping_service.get_by_session_id.return_value = [
            {
                "id": mapping_id,
                "source_role": "Software Engineer",
                "onet_code": "15-1252.00",
                "onet_title": "Software Developers",
                "confidence_score": 0.95,
                "is_confirmed": False,
            }
        ]

        response = client.get(f"/discovery/sessions/{session_id}/role-mappings")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == mapping_id
        assert data[0]["source_role"] == "Software Engineer"
        assert data[0]["onet_code"] == "15-1252.00"
        assert data[0]["onet_title"] == "Software Developers"
        assert data[0]["confidence_score"] == 0.95
        assert data[0]["is_confirmed"] is False
        mock_role_mapping_service.get_by_session_id.assert_called_once()

    def test_get_role_mappings_empty_list(self, client, mock_role_mapping_service):
        """Should return empty list when no mappings exist."""
        session_id = str(uuid4())
        mock_role_mapping_service.get_by_session_id.return_value = []

        response = client.get(f"/discovery/sessions/{session_id}/role-mappings")

        assert response.status_code == 200
        assert response.json() == []

    def test_get_role_mappings_validates_uuid(self, client, mock_role_mapping_service):
        """Should validate session ID is a valid UUID."""
        response = client.get("/discovery/sessions/not-a-uuid/role-mappings")

        assert response.status_code == 422


class TestUpdateRoleMapping:
    """Tests for PUT /discovery/role-mappings/{mapping_id}."""

    def test_update_role_mapping_returns_200(self, client, mock_role_mapping_service):
        """Should update role mapping and return 200."""
        mapping_id = str(uuid4())
        mock_role_mapping_service.update.return_value = {
            "id": mapping_id,
            "source_role": "Software Engineer",
            "onet_code": "15-1251.00",
            "onet_title": "Computer Programmers",
            "confidence_score": 1.0,
            "is_confirmed": True,
        }

        response = client.put(
            f"/discovery/role-mappings/{mapping_id}",
            json={"onet_code": "15-1251.00", "onet_title": "Computer Programmers", "is_confirmed": True},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["onet_code"] == "15-1251.00"
        assert data["onet_title"] == "Computer Programmers"
        assert data["is_confirmed"] is True
        mock_role_mapping_service.update.assert_called_once()

    def test_update_role_mapping_partial_update(self, client, mock_role_mapping_service):
        """Should allow partial update with only is_confirmed."""
        mapping_id = str(uuid4())
        mock_role_mapping_service.update.return_value = {
            "id": mapping_id,
            "source_role": "Software Engineer",
            "onet_code": "15-1252.00",
            "onet_title": "Software Developers",
            "confidence_score": 0.95,
            "is_confirmed": True,
        }

        response = client.put(
            f"/discovery/role-mappings/{mapping_id}",
            json={"is_confirmed": True},
        )

        assert response.status_code == 200
        assert response.json()["is_confirmed"] is True

    def test_update_role_mapping_not_found_returns_404(self, client, mock_role_mapping_service):
        """Should return 404 if mapping not found."""
        mapping_id = str(uuid4())
        mock_role_mapping_service.update.return_value = None

        response = client.put(
            f"/discovery/role-mappings/{mapping_id}",
            json={"is_confirmed": True},
        )

        assert response.status_code == 404

    def test_update_role_mapping_validates_uuid(self, client, mock_role_mapping_service):
        """Should validate mapping ID is a valid UUID."""
        response = client.put(
            "/discovery/role-mappings/not-a-uuid",
            json={"is_confirmed": True},
        )

        assert response.status_code == 422


class TestBulkConfirm:
    """Tests for POST /discovery/sessions/{session_id}/role-mappings/confirm."""

    def test_bulk_confirm_returns_200(self, client, mock_role_mapping_service):
        """Should bulk confirm mappings and return count."""
        session_id = str(uuid4())
        mock_role_mapping_service.bulk_confirm.return_value = {"confirmed_count": 5}

        response = client.post(
            f"/discovery/sessions/{session_id}/role-mappings/confirm",
            json={"threshold": 0.8},
        )

        assert response.status_code == 200
        assert response.json()["confirmed_count"] == 5
        mock_role_mapping_service.bulk_confirm.assert_called_once()

    def test_bulk_confirm_zero_threshold(self, client, mock_role_mapping_service):
        """Should accept threshold of 0."""
        session_id = str(uuid4())
        mock_role_mapping_service.bulk_confirm.return_value = {"confirmed_count": 10}

        response = client.post(
            f"/discovery/sessions/{session_id}/role-mappings/confirm",
            json={"threshold": 0.0},
        )

        assert response.status_code == 200
        assert response.json()["confirmed_count"] == 10

    def test_bulk_confirm_max_threshold(self, client, mock_role_mapping_service):
        """Should accept threshold of 1."""
        session_id = str(uuid4())
        mock_role_mapping_service.bulk_confirm.return_value = {"confirmed_count": 1}

        response = client.post(
            f"/discovery/sessions/{session_id}/role-mappings/confirm",
            json={"threshold": 1.0},
        )

        assert response.status_code == 200

    def test_bulk_confirm_invalid_threshold_above_1(self, client, mock_role_mapping_service):
        """Should reject threshold above 1."""
        session_id = str(uuid4())

        response = client.post(
            f"/discovery/sessions/{session_id}/role-mappings/confirm",
            json={"threshold": 1.5},
        )

        assert response.status_code == 422

    def test_bulk_confirm_invalid_threshold_below_0(self, client, mock_role_mapping_service):
        """Should reject threshold below 0."""
        session_id = str(uuid4())

        response = client.post(
            f"/discovery/sessions/{session_id}/role-mappings/confirm",
            json={"threshold": -0.1},
        )

        assert response.status_code == 422

    def test_bulk_confirm_validates_session_uuid(self, client, mock_role_mapping_service):
        """Should validate session ID is a valid UUID."""
        response = client.post(
            "/discovery/sessions/not-a-uuid/role-mappings/confirm",
            json={"threshold": 0.8},
        )

        assert response.status_code == 422


class TestOnetSearch:
    """Tests for GET /discovery/onet/search."""

    def test_search_onet_returns_200(self, client, mock_onet_service):
        """Should search O*NET occupations and return results."""
        mock_onet_service.search.return_value = [
            {"code": "15-1252.00", "title": "Software Developers", "score": 0.95},
            {"code": "15-1251.00", "title": "Computer Programmers", "score": 0.85},
        ]

        response = client.get("/discovery/onet/search", params={"q": "software engineer"})

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["code"] == "15-1252.00"
        assert data[0]["title"] == "Software Developers"
        assert data[0]["score"] == 0.95
        mock_onet_service.search.assert_called_once()

    def test_search_onet_empty_results(self, client, mock_onet_service):
        """Should return empty list when no matches found."""
        mock_onet_service.search.return_value = []

        response = client.get("/discovery/onet/search", params={"q": "xyz123nonexistent"})

        assert response.status_code == 200
        assert response.json() == []

    def test_search_onet_requires_query(self, client, mock_onet_service):
        """Should require query parameter."""
        response = client.get("/discovery/onet/search")

        assert response.status_code == 422

    def test_search_onet_empty_query(self, client, mock_onet_service):
        """Should reject empty query string."""
        response = client.get("/discovery/onet/search", params={"q": ""})

        assert response.status_code == 422


class TestOnetDetails:
    """Tests for GET /discovery/onet/{code}."""

    def test_get_onet_occupation_returns_200(self, client, mock_onet_service):
        """Should return O*NET occupation details."""
        mock_onet_service.get_occupation.return_value = {
            "code": "15-1252.00",
            "title": "Software Developers",
            "description": "Research, design, and develop computer and network software or specialized utility programs.",
            "gwas": [
                {"id": "1.A.1", "name": "Oral Comprehension", "importance": 75},
                {"id": "1.A.2", "name": "Written Comprehension", "importance": 72},
            ],
        }

        response = client.get("/discovery/onet/15-1252.00")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "15-1252.00"
        assert data["title"] == "Software Developers"
        assert data["description"] is not None
        assert len(data["gwas"]) == 2
        mock_onet_service.get_occupation.assert_called_once()

    def test_get_onet_occupation_without_optional_fields(self, client, mock_onet_service):
        """Should return occupation without optional fields."""
        mock_onet_service.get_occupation.return_value = {
            "code": "15-1252.00",
            "title": "Software Developers",
        }

        response = client.get("/discovery/onet/15-1252.00")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "15-1252.00"
        assert data["title"] == "Software Developers"
        assert data.get("description") is None
        assert data.get("gwas") is None

    def test_get_onet_occupation_not_found(self, client, mock_onet_service):
        """Should return 404 if occupation not found."""
        mock_onet_service.get_occupation.return_value = None

        response = client.get("/discovery/onet/99-9999.00")

        assert response.status_code == 404


class TestSchemas:
    """Tests for Pydantic schemas."""

    def test_role_mapping_response_fields(self):
        """RoleMappingResponse should have required fields."""
        from app.schemas.role_mapping import RoleMappingResponse

        mapping_id = uuid4()
        schema = RoleMappingResponse(
            id=mapping_id,
            source_role="Software Engineer",
            onet_code="15-1252.00",
            onet_title="Software Developers",
            confidence_score=0.95,
            is_confirmed=False,
        )

        assert schema.id == mapping_id
        assert schema.source_role == "Software Engineer"
        assert schema.onet_code == "15-1252.00"
        assert schema.onet_title == "Software Developers"
        assert schema.confidence_score == 0.95
        assert schema.is_confirmed is False

    def test_role_mapping_update_optional_fields(self):
        """RoleMappingUpdate should have optional fields."""
        from app.schemas.role_mapping import RoleMappingUpdate

        # All fields optional
        schema1 = RoleMappingUpdate()
        assert schema1.onet_code is None
        assert schema1.onet_title is None
        assert schema1.is_confirmed is None

        # Partial fields
        schema2 = RoleMappingUpdate(is_confirmed=True)
        assert schema2.is_confirmed is True

        # All fields
        schema3 = RoleMappingUpdate(
            onet_code="15-1251.00",
            onet_title="Computer Programmers",
            is_confirmed=True,
        )
        assert schema3.onet_code == "15-1251.00"

    def test_bulk_confirm_request_threshold_validation(self):
        """BulkConfirmRequest should validate threshold range."""
        from app.schemas.role_mapping import BulkConfirmRequest

        # Valid thresholds
        schema1 = BulkConfirmRequest(threshold=0.0)
        assert schema1.threshold == 0.0

        schema2 = BulkConfirmRequest(threshold=1.0)
        assert schema2.threshold == 1.0

        schema3 = BulkConfirmRequest(threshold=0.5)
        assert schema3.threshold == 0.5

        # Invalid thresholds
        with pytest.raises(ValueError):
            BulkConfirmRequest(threshold=-0.1)

        with pytest.raises(ValueError):
            BulkConfirmRequest(threshold=1.1)

    def test_bulk_confirm_response_fields(self):
        """BulkConfirmResponse should have confirmed_count."""
        from app.schemas.role_mapping import BulkConfirmResponse

        schema = BulkConfirmResponse(confirmed_count=5)
        assert schema.confirmed_count == 5

    def test_onet_occupation_fields(self):
        """OnetOccupation should have required and optional fields."""
        from app.schemas.role_mapping import OnetOccupation

        # Minimal fields
        schema1 = OnetOccupation(code="15-1252.00", title="Software Developers")
        assert schema1.code == "15-1252.00"
        assert schema1.title == "Software Developers"
        assert schema1.description is None
        assert schema1.gwas is None

        # All fields
        schema2 = OnetOccupation(
            code="15-1252.00",
            title="Software Developers",
            description="Develop software",
            gwas=[{"id": "1.A.1", "name": "Oral Comprehension", "importance": 75}],
        )
        assert schema2.description == "Develop software"
        assert len(schema2.gwas) == 1

    def test_onet_search_result_fields(self):
        """OnetSearchResult should have required fields."""
        from app.schemas.role_mapping import OnetSearchResult

        schema = OnetSearchResult(code="15-1252.00", title="Software Developers", score=0.95)
        assert schema.code == "15-1252.00"
        assert schema.title == "Software Developers"
        assert schema.score == 0.95
