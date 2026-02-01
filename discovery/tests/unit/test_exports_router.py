"""Tests for discovery exports router."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers.exports import router
from app.services.export_service import get_export_service
from app.schemas.export import HandoffBundle


@pytest.fixture
def mock_export_service():
    """Mock export service for testing."""
    service = MagicMock()
    service.generate_csv = AsyncMock()
    service.generate_xlsx = AsyncMock()
    service.generate_pdf = AsyncMock()
    service.generate_handoff_bundle = AsyncMock()
    return service


@pytest.fixture
def app(mock_export_service):
    """Create test FastAPI app with mocked dependencies."""
    app = FastAPI()
    app.include_router(router)

    # Override dependency
    app.dependency_overrides[get_export_service] = lambda: mock_export_service

    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


class TestExportCsv:
    """Tests for GET /discovery/sessions/{session_id}/export/csv."""

    def test_export_csv_returns_200_with_csv_content_type(self, client, mock_export_service):
        """Should return CSV file with correct content type."""
        session_id = uuid4()
        csv_content = b"role,department,activity\nManager,IT,Review reports"

        mock_export_service.generate_csv.return_value = csv_content

        response = client.get(f"/discovery/sessions/{session_id}/export/csv")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert response.content == csv_content
        mock_export_service.generate_csv.assert_called_once_with(session_id, None)

    def test_export_csv_returns_attachment_header(self, client, mock_export_service):
        """Should return content-disposition attachment header."""
        session_id = uuid4()
        csv_content = b"role,department,activity\nManager,IT,Review reports"

        mock_export_service.generate_csv.return_value = csv_content

        response = client.get(f"/discovery/sessions/{session_id}/export/csv")

        assert response.status_code == 200
        content_disposition = response.headers.get("content-disposition", "")
        assert "attachment" in content_disposition
        assert f"export_{session_id}.csv" in content_disposition

    def test_export_csv_with_dimension_filter(self, client, mock_export_service):
        """Should pass dimension filter to service."""
        session_id = uuid4()
        csv_content = b"role,activity\nManager,Review reports"

        mock_export_service.generate_csv.return_value = csv_content

        response = client.get(
            f"/discovery/sessions/{session_id}/export/csv",
            params={"dimension": "ROLE"},
        )

        assert response.status_code == 200
        mock_export_service.generate_csv.assert_called_once_with(session_id, "ROLE")

    def test_export_csv_session_not_found_returns_404(self, client, mock_export_service):
        """Should return 404 if session not found."""
        session_id = uuid4()
        mock_export_service.generate_csv.return_value = None

        response = client.get(f"/discovery/sessions/{session_id}/export/csv")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_export_csv_validates_uuid(self, client, mock_export_service):
        """Should validate session ID is a valid UUID."""
        response = client.get("/discovery/sessions/not-a-uuid/export/csv")

        assert response.status_code == 422


class TestExportXlsx:
    """Tests for GET /discovery/sessions/{session_id}/export/xlsx."""

    def test_export_xlsx_returns_200_with_xlsx_content_type(self, client, mock_export_service):
        """Should return Excel file with correct content type."""
        session_id = uuid4()
        xlsx_content = b"PK\x03\x04..."  # Mock XLSX binary content

        mock_export_service.generate_xlsx.return_value = xlsx_content

        response = client.get(f"/discovery/sessions/{session_id}/export/xlsx")

        assert response.status_code == 200
        expected_content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert response.headers["content-type"] == expected_content_type
        assert response.content == xlsx_content
        mock_export_service.generate_xlsx.assert_called_once_with(session_id)

    def test_export_xlsx_returns_attachment_header(self, client, mock_export_service):
        """Should return content-disposition attachment header."""
        session_id = uuid4()
        xlsx_content = b"PK\x03\x04..."

        mock_export_service.generate_xlsx.return_value = xlsx_content

        response = client.get(f"/discovery/sessions/{session_id}/export/xlsx")

        assert response.status_code == 200
        content_disposition = response.headers.get("content-disposition", "")
        assert "attachment" in content_disposition
        assert f"export_{session_id}.xlsx" in content_disposition

    def test_export_xlsx_session_not_found_returns_404(self, client, mock_export_service):
        """Should return 404 if session not found."""
        session_id = uuid4()
        mock_export_service.generate_xlsx.return_value = None

        response = client.get(f"/discovery/sessions/{session_id}/export/xlsx")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_export_xlsx_validates_uuid(self, client, mock_export_service):
        """Should validate session ID is a valid UUID."""
        response = client.get("/discovery/sessions/not-a-uuid/export/xlsx")

        assert response.status_code == 422


class TestExportPdf:
    """Tests for GET /discovery/sessions/{session_id}/export/pdf."""

    def test_export_pdf_returns_200_with_pdf_content_type(self, client, mock_export_service):
        """Should return PDF file with correct content type."""
        session_id = uuid4()
        pdf_content = b"%PDF-1.4..."  # Mock PDF binary content

        mock_export_service.generate_pdf.return_value = pdf_content

        response = client.get(f"/discovery/sessions/{session_id}/export/pdf")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert response.content == pdf_content
        mock_export_service.generate_pdf.assert_called_once_with(session_id)

    def test_export_pdf_returns_attachment_header(self, client, mock_export_service):
        """Should return content-disposition attachment header."""
        session_id = uuid4()
        pdf_content = b"%PDF-1.4..."

        mock_export_service.generate_pdf.return_value = pdf_content

        response = client.get(f"/discovery/sessions/{session_id}/export/pdf")

        assert response.status_code == 200
        content_disposition = response.headers.get("content-disposition", "")
        assert "attachment" in content_disposition
        assert f"report_{session_id}.pdf" in content_disposition

    def test_export_pdf_session_not_found_returns_404(self, client, mock_export_service):
        """Should return 404 if session not found."""
        session_id = uuid4()
        mock_export_service.generate_pdf.return_value = None

        response = client.get(f"/discovery/sessions/{session_id}/export/pdf")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_export_pdf_validates_uuid(self, client, mock_export_service):
        """Should validate session ID is a valid UUID."""
        response = client.get("/discovery/sessions/not-a-uuid/export/pdf")

        assert response.status_code == 422


class TestExportHandoff:
    """Tests for GET /discovery/sessions/{session_id}/export/handoff."""

    def test_export_handoff_returns_200_with_json(self, client, mock_export_service):
        """Should return handoff bundle as JSON."""
        session_id = uuid4()
        handoff_data = {
            "session_summary": {"id": str(session_id), "name": "Test Session"},
            "role_mappings": [{"role": "Manager", "onet_code": "11-1011.00"}],
            "analysis_results": [{"dimension": "ROLE", "score": 85}],
            "roadmap": [{"phase": 1, "name": "Quick Wins"}],
        }

        mock_export_service.generate_handoff_bundle.return_value = handoff_data

        response = client.get(f"/discovery/sessions/{session_id}/export/handoff")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        data = response.json()
        assert "session_summary" in data
        assert "role_mappings" in data
        assert "analysis_results" in data
        assert "roadmap" in data
        mock_export_service.generate_handoff_bundle.assert_called_once_with(session_id)

    def test_export_handoff_session_not_found_returns_404(self, client, mock_export_service):
        """Should return 404 if session not found."""
        session_id = uuid4()
        mock_export_service.generate_handoff_bundle.return_value = None

        response = client.get(f"/discovery/sessions/{session_id}/export/handoff")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_export_handoff_validates_uuid(self, client, mock_export_service):
        """Should validate session ID is a valid UUID."""
        response = client.get("/discovery/sessions/not-a-uuid/export/handoff")

        assert response.status_code == 422

    def test_export_handoff_returns_all_required_fields(self, client, mock_export_service):
        """Should return response with all required HandoffBundle fields."""
        session_id = uuid4()
        handoff_data = {
            "session_summary": {"id": str(session_id)},
            "role_mappings": [],
            "analysis_results": [],
            "roadmap": [],
        }

        mock_export_service.generate_handoff_bundle.return_value = handoff_data

        response = client.get(f"/discovery/sessions/{session_id}/export/handoff")

        assert response.status_code == 200
        data = response.json()
        # Verify all required fields are present
        assert isinstance(data["session_summary"], dict)
        assert isinstance(data["role_mappings"], list)
        assert isinstance(data["analysis_results"], list)
        assert isinstance(data["roadmap"], list)


class TestHandoffBundleSchema:
    """Tests for HandoffBundle Pydantic schema."""

    def test_handoff_bundle_has_required_fields(self):
        """HandoffBundle should have all required fields."""
        bundle = HandoffBundle(
            session_summary={"id": "test-id"},
            role_mappings=[{"role": "Manager"}],
            analysis_results=[{"score": 85}],
            roadmap=[{"phase": 1}],
        )
        assert bundle.session_summary == {"id": "test-id"}
        assert bundle.role_mappings == [{"role": "Manager"}]
        assert bundle.analysis_results == [{"score": 85}]
        assert bundle.roadmap == [{"phase": 1}]

    def test_handoff_bundle_accepts_empty_lists(self):
        """HandoffBundle should accept empty lists."""
        bundle = HandoffBundle(
            session_summary={},
            role_mappings=[],
            analysis_results=[],
            roadmap=[],
        )
        assert bundle.session_summary == {}
        assert bundle.role_mappings == []
        assert bundle.analysis_results == []
        assert bundle.roadmap == []

    def test_handoff_bundle_accepts_complex_data(self):
        """HandoffBundle should accept complex nested data."""
        bundle = HandoffBundle(
            session_summary={
                "id": "123",
                "name": "Test",
                "metadata": {"created": "2024-01-01", "steps_completed": 5},
            },
            role_mappings=[
                {"role": "Manager", "onet_code": "11-1011.00", "activities": ["a1", "a2"]},
                {"role": "Analyst", "onet_code": "15-2041.00", "activities": ["a3"]},
            ],
            analysis_results=[
                {"dimension": "ROLE", "score": 85, "details": {"items": 10}},
            ],
            roadmap=[
                {"phase": 1, "name": "Quick Wins", "items": [{"id": 1}, {"id": 2}]},
            ],
        )
        assert bundle.session_summary["metadata"]["steps_completed"] == 5
        assert len(bundle.role_mappings) == 2
        assert bundle.analysis_results[0]["dimension"] == "ROLE"
        assert bundle.roadmap[0]["name"] == "Quick Wins"
