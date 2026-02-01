# backend/tests/unit/modules/discovery/test_onet_client.py
"""Unit tests for O*NET API client."""

import pytest
from unittest.mock import AsyncMock, patch

from app.modules.discovery.services.onet_client import OnetApiClient


@pytest.fixture
def onet_client():
    """Create an OnetApiClient instance for testing."""
    return OnetApiClient(api_key="test_key")


def test_onet_client_init():
    """OnetApiClient should initialize with API key."""
    client = OnetApiClient(api_key="my_key")
    assert client.api_key == "my_key"
    assert client.base_url == "https://services.onetcenter.org/ws/"


def test_onet_client_auth_header(onet_client):
    """OnetApiClient should create basic auth header."""
    auth = onet_client._get_auth()
    assert auth is not None


@pytest.mark.asyncio
async def test_search_occupations(onet_client):
    """Should search O*NET occupations by keyword."""
    mock_response = {
        "occupation": [
            {"code": "15-1252.00", "title": "Software Developers"},
            {"code": "15-1251.00", "title": "Computer Programmers"},
        ]
    }

    with patch.object(onet_client, "_get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response

        results = await onet_client.search_occupations("software")

        assert len(results) == 2
        assert results[0]["code"] == "15-1252.00"


@pytest.mark.asyncio
async def test_search_occupations_empty(onet_client):
    """Should return empty list when no occupations found."""
    mock_response = {}

    with patch.object(onet_client, "_get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response

        results = await onet_client.search_occupations("nonexistent")

        assert results == []


@pytest.mark.asyncio
async def test_get_occupation_tasks(onet_client):
    """Should fetch tasks for an occupation."""
    mock_response = {
        "task": [
            {"id": "1", "statement": "Analyze user needs"},
            {"id": "2", "statement": "Write code"},
        ]
    }

    with patch.object(onet_client, "_get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response

        tasks = await onet_client.get_occupation_tasks("15-1252.00")

        assert len(tasks) == 2


@pytest.mark.asyncio
async def test_get_occupation_tasks_empty(onet_client):
    """Should return empty list when no tasks found."""
    mock_response = {}

    with patch.object(onet_client, "_get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response

        tasks = await onet_client.get_occupation_tasks("00-0000.00")

        assert tasks == []


@pytest.mark.asyncio
async def test_get_work_activities(onet_client):
    """Should fetch work activities for an occupation."""
    mock_response = {
        "element": [
            {"id": "4.A.1.a.1", "name": "Getting Information"},
        ]
    }

    with patch.object(onet_client, "_get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response

        activities = await onet_client.get_work_activities("15-1252.00")

        assert len(activities) >= 1


@pytest.mark.asyncio
async def test_get_work_activities_empty(onet_client):
    """Should return empty list when no activities found."""
    mock_response = {}

    with patch.object(onet_client, "_get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response

        activities = await onet_client.get_work_activities("00-0000.00")

        assert activities == []


def test_rate_limiting(onet_client):
    """Should respect rate limits (10 req/sec)."""
    assert onet_client.rate_limit == 10


@pytest.mark.asyncio
async def test_get_occupation_details(onet_client):
    """Should fetch full occupation details."""
    mock_response = {
        "code": "15-1252.00",
        "title": "Software Developers",
        "description": "Research, design, and develop computer software.",
    }

    with patch.object(onet_client, "_get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response

        details = await onet_client.get_occupation_details("15-1252.00")

        assert details["code"] == "15-1252.00"
        assert details["title"] == "Software Developers"


@pytest.mark.asyncio
async def test_get_skills(onet_client):
    """Should fetch skills for an occupation."""
    mock_response = {
        "element": [
            {"id": "2.A.1.a", "name": "Reading Comprehension"},
            {"id": "2.A.1.b", "name": "Active Listening"},
        ]
    }

    with patch.object(onet_client, "_get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response

        skills = await onet_client.get_skills("15-1252.00")

        assert len(skills) == 2
        assert skills[0]["name"] == "Reading Comprehension"


@pytest.mark.asyncio
async def test_get_technology_skills(onet_client):
    """Should fetch technology skills for an occupation."""
    mock_response = {
        "category": [
            {
                "title": {"name": "Development environment software"},
                "example": [{"name": "Microsoft Visual Studio"}],
            }
        ]
    }

    with patch.object(onet_client, "_get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response

        tech_skills = await onet_client.get_technology_skills("15-1252.00")

        assert len(tech_skills) >= 1
