# discovery/tests/integration/routers/test_sessions_router.py
"""Integration tests for sessions router."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from uuid import uuid4

from app.main import app
from app.services.session_service import SessionService, get_session_service


@pytest.fixture
def mock_session_service():
    """Create a mock session service."""
    mock = AsyncMock(spec=SessionService)
    return mock


@pytest.fixture
def client(mock_session_service):
    """Create test client with mocked dependencies."""
    app.dependency_overrides[get_session_service] = lambda: mock_session_service
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_create_session(client, mock_session_service):
    """Test POST /discovery/sessions creates a session."""
    mock_result = {
        "id": str(uuid4()),
        "status": "draft",
        "current_step": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    mock_session_service.create.return_value = mock_result

    response = client.post(
        "/discovery/sessions",
        json={"organization_id": str(uuid4())},
    )

    assert response.status_code == 201
    assert "id" in response.json()


def test_get_session(client, mock_session_service):
    """Test GET /discovery/sessions/{id} returns session."""
    session_id = uuid4()
    mock_result = {
        "id": str(session_id),
        "status": "draft",
        "current_step": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    mock_session_service.get_by_id.return_value = mock_result

    response = client.get(f"/discovery/sessions/{session_id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(session_id)


def test_get_session_not_found(client, mock_session_service):
    """Test GET /discovery/sessions/{id} returns 404 for missing session."""
    session_id = uuid4()
    mock_session_service.get_by_id.return_value = None

    response = client.get(f"/discovery/sessions/{session_id}")

    assert response.status_code == 404
