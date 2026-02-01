"""Tests for discovery upload router."""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from io import BytesIO

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers.uploads import router, get_upload_service


@pytest.fixture
def mock_upload_service():
    """Mock upload service for testing."""
    service = MagicMock()
    service.process_upload = AsyncMock()
    service.get_by_session_id = AsyncMock()
    service.update_column_mappings = AsyncMock()
    return service


@pytest.fixture
def app(mock_upload_service):
    """Create test FastAPI app with mocked dependencies."""
    app = FastAPI()
    app.include_router(router)

    # Override dependency
    app.dependency_overrides[get_upload_service] = lambda: mock_upload_service

    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


class TestUploadFile:
    """Tests for POST /discovery/sessions/{id}/upload."""

    def test_upload_csv_returns_201(self, client, mock_upload_service):
        """Should upload CSV and return 201."""
        session_id = str(uuid4())
        upload_id = str(uuid4())
        now = datetime.now(timezone.utc)

        mock_upload_service.process_upload.return_value = {
            "id": upload_id,
            "file_name": "data.csv",
            "row_count": 100,
            "detected_schema": ["Name", "Role", "Department"],
            "created_at": now.isoformat(),
        }

        csv_content = b"Name,Role,Department\nJohn,Engineer,IT"
        response = client.post(
            f"/discovery/sessions/{session_id}/upload",
            files={"file": ("data.csv", BytesIO(csv_content), "text/csv")},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["file_name"] == "data.csv"
        assert data["row_count"] == 100
        assert data["detected_schema"] == ["Name", "Role", "Department"]
        assert data["id"] == upload_id
        mock_upload_service.process_upload.assert_called_once()

    def test_upload_xlsx_returns_201(self, client, mock_upload_service):
        """Should upload XLSX and return 201."""
        session_id = str(uuid4())
        upload_id = str(uuid4())
        now = datetime.now(timezone.utc)

        mock_upload_service.process_upload.return_value = {
            "id": upload_id,
            "file_name": "data.xlsx",
            "row_count": 50,
            "detected_schema": ["Employee", "Title"],
            "created_at": now.isoformat(),
        }

        # Minimal XLSX content (just bytes for testing - real validation happens in service)
        xlsx_content = b"PK\x03\x04..."
        response = client.post(
            f"/discovery/sessions/{session_id}/upload",
            files={
                "file": (
                    "data.xlsx",
                    BytesIO(xlsx_content),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["file_name"] == "data.xlsx"
        mock_upload_service.process_upload.assert_called_once()

    def test_upload_invalid_type_returns_400(self, client, mock_upload_service):
        """Should reject unsupported file types."""
        session_id = str(uuid4())

        response = client.post(
            f"/discovery/sessions/{session_id}/upload",
            files={"file": ("report.pdf", BytesIO(b"pdf content"), "application/pdf")},
        )

        assert response.status_code == 400
        assert "unsupported" in response.json()["detail"].lower()
        mock_upload_service.process_upload.assert_not_called()

    def test_upload_too_large_returns_413(self, client, mock_upload_service):
        """Should reject files exceeding size limit."""
        session_id = str(uuid4())
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB

        response = client.post(
            f"/discovery/sessions/{session_id}/upload",
            files={"file": ("huge.csv", BytesIO(large_content), "text/csv")},
        )

        assert response.status_code == 413
        assert "too large" in response.json()["detail"].lower()
        mock_upload_service.process_upload.assert_not_called()

    def test_upload_validates_session_id_format(self, client, mock_upload_service):
        """Should validate session ID is a valid UUID."""
        csv_content = b"Name,Role\nJohn,Engineer"

        response = client.post(
            "/discovery/sessions/not-a-uuid/upload",
            files={"file": ("data.csv", BytesIO(csv_content), "text/csv")},
        )

        assert response.status_code == 422

    def test_upload_empty_file(self, client, mock_upload_service):
        """Should reject empty files with 400."""
        session_id = str(uuid4())

        response = client.post(
            f"/discovery/sessions/{session_id}/upload",
            files={"file": ("empty.csv", BytesIO(b""), "text/csv")},
        )

        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()
        mock_upload_service.process_upload.assert_not_called()

    def test_upload_with_special_chars_filename(self, client, mock_upload_service):
        """Should sanitize filename with special characters to 'unknown'."""
        session_id = str(uuid4())
        upload_id = str(uuid4())
        now = datetime.now(timezone.utc)

        mock_upload_service.process_upload.return_value = {
            "id": upload_id,
            "file_name": "unknown",
            "row_count": 100,
            "detected_schema": ["Name", "Role"],
            "created_at": now.isoformat(),
        }

        csv_content = b"Name,Role\nJohn,Engineer"
        # Filename with only special characters should become "unknown"
        response = client.post(
            f"/discovery/sessions/{session_id}/upload",
            files={"file": ("@#$%^&*()", BytesIO(csv_content), "text/csv")},
        )

        assert response.status_code == 201
        # Verify service was called with sanitized filename
        call_args = mock_upload_service.process_upload.call_args
        assert call_args.kwargs["file_name"] == "unknown"

    def test_upload_file_at_exact_size_limit(self, client, mock_upload_service):
        """Should accept file at exactly 10MB."""
        session_id = str(uuid4())
        upload_id = str(uuid4())
        now = datetime.now(timezone.utc)

        mock_upload_service.process_upload.return_value = {
            "id": upload_id,
            "file_name": "large.csv",
            "row_count": 500000,
            "detected_schema": ["Data"],
            "created_at": now.isoformat(),
        }

        # Create content at exactly 10MB
        exact_limit_content = b"x" * (10 * 1024 * 1024)
        response = client.post(
            f"/discovery/sessions/{session_id}/upload",
            files={"file": ("large.csv", BytesIO(exact_limit_content), "text/csv")},
        )

        assert response.status_code == 201
        mock_upload_service.process_upload.assert_called_once()

    def test_upload_csv_with_charset_header(self, client, mock_upload_service):
        """Should accept CSV with charset in content-type."""
        session_id = str(uuid4())
        upload_id = str(uuid4())
        now = datetime.now(timezone.utc)

        mock_upload_service.process_upload.return_value = {
            "id": upload_id,
            "file_name": "data.csv",
            "row_count": 100,
            "detected_schema": ["Name", "Role"],
            "created_at": now.isoformat(),
        }

        csv_content = b"Name,Role\nJohn,Engineer"
        response = client.post(
            f"/discovery/sessions/{session_id}/upload",
            files={"file": ("data.csv", BytesIO(csv_content), "text/csv; charset=utf-8")},
        )

        assert response.status_code == 201
        mock_upload_service.process_upload.assert_called_once()

    def test_upload_spoofed_xlsx_content_type(self, client, mock_upload_service):
        """Should reject file with XLSX content-type but invalid content."""
        session_id = str(uuid4())

        # Send text content claiming to be XLSX
        fake_xlsx_content = b"This is not an XLSX file"
        response = client.post(
            f"/discovery/sessions/{session_id}/upload",
            files={
                "file": (
                    "fake.xlsx",
                    BytesIO(fake_xlsx_content),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
        )

        assert response.status_code == 400
        assert "xlsx" in response.json()["detail"].lower()
        mock_upload_service.process_upload.assert_not_called()

    def test_upload_sanitizes_path_traversal_filename(self, client, mock_upload_service):
        """Should sanitize filenames with path traversal attempts."""
        session_id = str(uuid4())
        upload_id = str(uuid4())
        now = datetime.now(timezone.utc)

        mock_upload_service.process_upload.return_value = {
            "id": upload_id,
            "file_name": "data.csv",
            "row_count": 100,
            "detected_schema": ["Name"],
            "created_at": now.isoformat(),
        }

        csv_content = b"Name\nJohn"
        response = client.post(
            f"/discovery/sessions/{session_id}/upload",
            files={"file": ("../../../etc/passwd", BytesIO(csv_content), "text/csv")},
        )

        assert response.status_code == 201
        # Verify filename was sanitized (path separators removed)
        call_args = mock_upload_service.process_upload.call_args
        assert "/" not in call_args.kwargs["file_name"]
        assert ".." not in call_args.kwargs["file_name"]


class TestListUploads:
    """Tests for GET /discovery/sessions/{id}/uploads."""

    def test_list_uploads_returns_200(self, client, mock_upload_service):
        """Should return list of uploads."""
        session_id = str(uuid4())
        upload_id = str(uuid4())
        now = datetime.now(timezone.utc)

        mock_upload_service.get_by_session_id.return_value = [
            {
                "id": upload_id,
                "file_name": "data.csv",
                "row_count": 100,
                "detected_schema": ["Name", "Role"],
                "created_at": now.isoformat(),
            }
        ]

        response = client.get(f"/discovery/sessions/{session_id}/uploads")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["file_name"] == "data.csv"
        assert data[0]["row_count"] == 100
        mock_upload_service.get_by_session_id.assert_called_once()

    def test_list_uploads_empty_returns_empty_list(self, client, mock_upload_service):
        """Should return empty list when no uploads exist."""
        session_id = str(uuid4())
        mock_upload_service.get_by_session_id.return_value = []

        response = client.get(f"/discovery/sessions/{session_id}/uploads")

        assert response.status_code == 200
        assert response.json() == []

    def test_list_uploads_validates_session_id(self, client, mock_upload_service):
        """Should validate session ID is a valid UUID."""
        response = client.get("/discovery/sessions/not-a-uuid/uploads")

        assert response.status_code == 422


class TestUpdateMappings:
    """Tests for PUT /discovery/uploads/{id}/mappings."""

    def test_update_mappings_returns_200(self, client, mock_upload_service):
        """Should update column mappings."""
        upload_id = str(uuid4())
        now = datetime.now(timezone.utc)

        mock_upload_service.update_column_mappings.return_value = {
            "id": upload_id,
            "file_name": "data.csv",
            "row_count": 100,
            "detected_schema": ["Column A", "Column B", "Column C"],
            "column_mappings": {"role": "Column B", "department": "Column C"},
            "created_at": now.isoformat(),
        }

        response = client.put(
            f"/discovery/uploads/{upload_id}/mappings",
            json={"role": "Column B", "department": "Column C"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["column_mappings"]["role"] == "Column B"
        assert data["column_mappings"]["department"] == "Column C"
        mock_upload_service.update_column_mappings.assert_called_once()

    def test_update_mappings_with_geography(self, client, mock_upload_service):
        """Should support geography mapping."""
        upload_id = str(uuid4())
        now = datetime.now(timezone.utc)

        mock_upload_service.update_column_mappings.return_value = {
            "id": upload_id,
            "file_name": "data.csv",
            "row_count": 100,
            "detected_schema": ["Name", "Role", "Dept", "Location"],
            "column_mappings": {
                "role": "Role",
                "department": "Dept",
                "geography": "Location",
            },
            "created_at": now.isoformat(),
        }

        response = client.put(
            f"/discovery/uploads/{upload_id}/mappings",
            json={"role": "Role", "department": "Dept", "geography": "Location"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["column_mappings"]["geography"] == "Location"

    def test_update_mappings_validates_upload_id(self, client, mock_upload_service):
        """Should validate upload ID is a valid UUID."""
        response = client.put(
            "/discovery/uploads/not-a-uuid/mappings",
            json={"role": "Column B"},
        )

        assert response.status_code == 422

    def test_update_mappings_not_found_returns_404(self, client, mock_upload_service):
        """Should return 404 if upload not found."""
        upload_id = str(uuid4())
        mock_upload_service.update_column_mappings.return_value = None

        response = client.put(
            f"/discovery/uploads/{upload_id}/mappings",
            json={"role": "Column B"},
        )

        assert response.status_code == 404


class TestSchemas:
    """Tests for Pydantic schemas."""

    def test_upload_response_has_required_fields(self):
        """UploadResponse should have all required fields."""
        from app.schemas.upload import UploadResponse

        upload_id = uuid4()
        now = datetime.now(timezone.utc)

        schema = UploadResponse(
            id=upload_id,
            file_name="data.csv",
            row_count=100,
            detected_schema=["Name", "Role"],
            created_at=now,
        )

        assert schema.id == upload_id
        assert schema.file_name == "data.csv"
        assert schema.row_count == 100
        assert schema.detected_schema == ["Name", "Role"]
        assert schema.created_at == now

    def test_upload_response_optional_mappings(self):
        """UploadResponse should have optional column_mappings."""
        from app.schemas.upload import UploadResponse

        upload_id = uuid4()
        now = datetime.now(timezone.utc)

        schema = UploadResponse(
            id=upload_id,
            file_name="data.csv",
            row_count=100,
            detected_schema=["Name", "Role"],
            created_at=now,
            column_mappings={"role": "Role"},
        )

        assert schema.column_mappings == {"role": "Role"}

    def test_column_mapping_update_fields(self):
        """ColumnMappingUpdate should have role, department, geography fields."""
        from app.schemas.upload import ColumnMappingUpdate

        schema = ColumnMappingUpdate(
            role="Column A",
            department="Column B",
            geography="Column C",
        )

        assert schema.role == "Column A"
        assert schema.department == "Column B"
        assert schema.geography == "Column C"

    def test_column_mapping_update_optional_fields(self):
        """ColumnMappingUpdate fields should be optional."""
        from app.schemas.upload import ColumnMappingUpdate

        schema = ColumnMappingUpdate(role="Column A")

        assert schema.role == "Column A"
        assert schema.department is None
        assert schema.geography is None
