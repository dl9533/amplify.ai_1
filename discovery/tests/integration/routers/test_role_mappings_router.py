# discovery/tests/integration/routers/test_role_mappings_router.py
"""Integration tests for role mappings router."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock
from uuid import uuid4

from app.main import app
from app.services.role_mapping_service import (
    RoleMappingService,
    get_role_mapping_service,
)


@pytest.fixture
def mock_role_mapping_service():
    """Create a mock role mapping service."""
    mock = AsyncMock(spec=RoleMappingService)
    return mock


@pytest.fixture
def client(mock_role_mapping_service):
    """Create test client with mocked dependencies."""
    app.dependency_overrides[get_role_mapping_service] = lambda: mock_role_mapping_service
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_get_role_mappings(client, mock_role_mapping_service):
    """Test GET /discovery/sessions/{id}/role-mappings lists mappings."""
    session_id = uuid4()
    mock_results = [
        {
            "id": str(uuid4()),
            "source_role": "Software Engineer",
            "onet_code": "15-1252.00",
            "onet_title": "Software Developers",
            "confidence_score": 0.95,
            "is_confirmed": False,
        },
        {
            "id": str(uuid4()),
            "source_role": "Data Analyst",
            "onet_code": "15-2051.00",
            "onet_title": "Data Scientists",
            "confidence_score": 0.87,
            "is_confirmed": True,
        },
    ]
    mock_role_mapping_service.get_by_session_id.return_value = mock_results

    response = client.get(f"/discovery/sessions/{session_id}/role-mappings")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["source_role"] == "Software Engineer"


def test_update_role_mapping(client, mock_role_mapping_service):
    """Test PUT /discovery/role-mappings/{id} updates mapping."""
    mapping_id = uuid4()
    mock_result = {
        "id": str(mapping_id),
        "source_role": "Engineer",
        "onet_code": "15-1252.00",
        "onet_title": "Software Developers",
        "confidence_score": 0.95,
        "is_confirmed": True,
    }
    mock_role_mapping_service.update.return_value = mock_result

    response = client.put(
        f"/discovery/role-mappings/{mapping_id}",
        json={"is_confirmed": True},
    )

    assert response.status_code == 200
    assert response.json()["is_confirmed"] is True


def test_bulk_confirm_mappings(client, mock_role_mapping_service):
    """Test POST /discovery/sessions/{id}/role-mappings/confirm."""
    session_id = uuid4()
    mock_role_mapping_service.bulk_confirm.return_value = {"confirmed_count": 5}

    response = client.post(
        f"/discovery/sessions/{session_id}/role-mappings/confirm",
        json={"threshold": 0.8},
    )

    assert response.status_code == 200
    assert response.json()["confirmed_count"] == 5
