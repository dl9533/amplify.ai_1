# discovery/tests/integration/routers/test_uploads_router.py
"""Integration tests for uploads router."""
import pytest
import io
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock
from datetime import datetime, timezone
from uuid import uuid4

from app.main import app
from app.services.upload_service import UploadService, get_upload_service


@pytest.fixture
def mock_upload_service():
    """Create a mock upload service."""
    mock = AsyncMock(spec=UploadService)
    return mock


@pytest.fixture
def client(mock_upload_service):
    """Create test client with mocked dependencies."""
    app.dependency_overrides[get_upload_service] = lambda: mock_upload_service
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_upload_file(client, mock_upload_service):
    """Test POST /discovery/sessions/{id}/upload uploads file."""
    session_id = uuid4()
    upload_id = uuid4()
    mock_result = {
        "id": str(upload_id),
        "file_name": "test.csv",
        "row_count": 100,
        "detected_schema": ["name", "role"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "column_mappings": None,
    }
    mock_upload_service.process_upload.return_value = mock_result

    csv_content = b"name,role\nJohn,Engineer\nJane,Manager"
    files = {"file": ("test.csv", io.BytesIO(csv_content), "text/csv")}

    response = client.post(
        f"/discovery/sessions/{session_id}/upload",
        files=files,
    )

    assert response.status_code == 201
    assert response.json()["file_name"] == "test.csv"


def test_list_uploads(client, mock_upload_service):
    """Test GET /discovery/sessions/{id}/uploads lists uploads."""
    session_id = uuid4()
    mock_results = [
        {
            "id": str(uuid4()),
            "file_name": "file1.csv",
            "row_count": 50,
            "detected_schema": ["a", "b"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "column_mappings": None,
        },
        {
            "id": str(uuid4()),
            "file_name": "file2.csv",
            "row_count": 75,
            "detected_schema": ["x", "y"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "column_mappings": {"role_column": "y"},
        },
    ]
    mock_upload_service.get_by_session_id.return_value = mock_results

    response = client.get(f"/discovery/sessions/{session_id}/uploads")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_upload_invalid_file_type(client, mock_upload_service):
    """Test upload rejects invalid file types."""
    session_id = uuid4()

    files = {"file": ("test.pdf", io.BytesIO(b"PDF content"), "application/pdf")}

    response = client.post(
        f"/discovery/sessions/{session_id}/upload",
        files=files,
    )

    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]
