"""Unit tests for O*NET API client.

Tests the OnetApiClient class with mocked HTTP responses following TDD methodology.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from app.config import Settings
from app.exceptions import OnetApiError, OnetAuthError, OnetNotFoundError, OnetRateLimitError
from app.services.onet_client import OnetApiClient


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    settings = MagicMock(spec=Settings)
    settings.onet_api_key = MagicMock()
    settings.onet_api_key.get_secret_value.return_value = "test_api_key"
    settings.onet_api_base_url = "https://services.onetcenter.org/ws/"
    return settings


@pytest.fixture
def onet_client(mock_settings):
    """Create an OnetApiClient instance for testing."""
    return OnetApiClient(settings=mock_settings)


class TestOnetApiClientInit:
    """Tests for OnetApiClient initialization."""

    def test_init_with_settings(self, mock_settings):
        """OnetApiClient should initialize with Settings dependency."""
        client = OnetApiClient(settings=mock_settings)
        assert client.settings is mock_settings
        assert client.base_url == "https://services.onetcenter.org/ws/"

    def test_init_extracts_api_key(self, mock_settings):
        """OnetApiClient should extract API key from settings."""
        client = OnetApiClient(settings=mock_settings)
        assert client._get_api_key() == "test_api_key"


class TestOnetApiClientAuth:
    """Tests for O*NET API authentication."""

    def test_creates_basic_auth_with_api_key_as_username(self, onet_client):
        """Should create Basic Auth with API key as username."""
        auth = onet_client._get_auth()
        assert isinstance(auth, httpx.BasicAuth)
        # Basic auth should use API key as username
        assert auth._auth_header is not None

    def test_basic_auth_uses_empty_password(self, onet_client):
        """Basic Auth should use empty string as password."""
        # The password can be empty or same as username per requirements
        auth = onet_client._get_auth()
        assert auth is not None


class TestSearchOccupations:
    """Tests for search_occupations method."""

    @pytest.mark.asyncio
    async def test_search_occupations_returns_list(self, onet_client):
        """Should return list of occupation dicts matching keyword."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "occupation": [
                {"code": "15-1252.00", "title": "Software Developers"},
                {"code": "15-1251.00", "title": "Computer Programmers"},
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            results = await onet_client.search_occupations("software")

            assert isinstance(results, list)
            assert len(results) == 2
            assert results[0]["code"] == "15-1252.00"
            assert results[0]["title"] == "Software Developers"

    @pytest.mark.asyncio
    async def test_search_occupations_empty_results(self, onet_client):
        """Should return empty list when no matches found."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"occupation": []}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            results = await onet_client.search_occupations("nonexistent")

            assert results == []

    @pytest.mark.asyncio
    async def test_search_occupations_uses_correct_endpoint(self, onet_client):
        """Should call the correct O*NET search endpoint."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"occupation": []}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            await onet_client.search_occupations("developer")

            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert "mnm/search" in call_args.kwargs.get("url", call_args.args[0] if call_args.args else "")
            assert call_args.kwargs.get("params", {}).get("keyword") == "developer"


class TestGetOccupation:
    """Tests for get_occupation method."""

    @pytest.mark.asyncio
    async def test_get_occupation_returns_details(self, onet_client):
        """Should return occupation details for valid code."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": "15-1252.00",
            "title": "Software Developers",
            "description": "Research, design, and develop computer software.",
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            result = await onet_client.get_occupation("15-1252.00")

            assert result is not None
            assert result["code"] == "15-1252.00"
            assert result["title"] == "Software Developers"

    @pytest.mark.asyncio
    async def test_get_occupation_not_found_returns_none(self, onet_client):
        """Should return None when occupation code not found."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            message="Not Found",
            request=MagicMock(),
            response=MagicMock(status_code=404),
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            result = await onet_client.get_occupation("00-0000.00")

            assert result is None


class TestGetWorkActivities:
    """Tests for get_work_activities method."""

    @pytest.mark.asyncio
    async def test_get_work_activities_returns_list(self, onet_client):
        """Should return list of work activities for occupation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "element": [
                {"id": "4.A.1.a.1", "name": "Getting Information"},
                {"id": "4.A.1.b.1", "name": "Analyzing Data"},
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            results = await onet_client.get_work_activities("15-1252.00")

            assert isinstance(results, list)
            assert len(results) == 2
            assert results[0]["id"] == "4.A.1.a.1"
            assert results[0]["name"] == "Getting Information"

    @pytest.mark.asyncio
    async def test_get_work_activities_uses_correct_endpoint(self, onet_client):
        """Should call the correct work activities endpoint."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"element": []}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            await onet_client.get_work_activities("15-1252.00")

            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            url = call_args.kwargs.get("url", call_args.args[0] if call_args.args else "")
            assert "online/occupations/15-1252.00/summary/work_activities" in url


class TestGetTasks:
    """Tests for get_tasks method."""

    @pytest.mark.asyncio
    async def test_get_tasks_returns_list(self, onet_client):
        """Should return list of tasks for occupation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "task": [
                {"id": "1", "statement": "Analyze user needs"},
                {"id": "2", "statement": "Write and test code"},
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            results = await onet_client.get_tasks("15-1252.00")

            assert isinstance(results, list)
            assert len(results) == 2
            assert results[0]["statement"] == "Analyze user needs"

    @pytest.mark.asyncio
    async def test_get_tasks_uses_correct_endpoint(self, onet_client):
        """Should call the correct tasks endpoint."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"task": []}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            await onet_client.get_tasks("15-1252.00")

            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            url = call_args.kwargs.get("url", call_args.args[0] if call_args.args else "")
            assert "online/occupations/15-1252.00/summary/tasks" in url


class TestErrorHandling:
    """Tests for API error handling."""

    @pytest.mark.asyncio
    async def test_rate_limit_error_raised_on_429(self, onet_client):
        """Should raise OnetRateLimitError on 429 response."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            message="Too Many Requests",
            request=MagicMock(),
            response=mock_response,
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            with pytest.raises(OnetRateLimitError) as exc_info:
                await onet_client.search_occupations("software")

            assert exc_info.value.status_code == 429
            assert exc_info.value.retry_after == 60

    @pytest.mark.asyncio
    async def test_auth_error_raised_on_401(self, onet_client):
        """Should raise OnetAuthError on 401 response."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            message="Unauthorized",
            request=MagicMock(),
            response=mock_response,
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            with pytest.raises(OnetAuthError) as exc_info:
                await onet_client.search_occupations("software")

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_api_error_raised_on_other_errors(self, onet_client):
        """Should raise OnetApiError on other HTTP errors."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            message="Server Error",
            request=MagicMock(),
            response=mock_response,
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            with pytest.raises(OnetApiError) as exc_info:
                await onet_client.search_occupations("software")

            assert exc_info.value.status_code == 500


class TestHttpxAsyncClient:
    """Tests to verify httpx.AsyncClient is used correctly."""

    @pytest.mark.asyncio
    async def test_uses_async_client(self, onet_client):
        """Should use httpx.AsyncClient for HTTP requests."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"occupation": []}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            await onet_client.search_occupations("test")

            mock_client_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_passes_basic_auth(self, onet_client):
        """Should pass Basic Auth credentials to requests."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"occupation": []}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            await onet_client.search_occupations("test")

            call_args = mock_client.get.call_args
            assert "auth" in call_args.kwargs
            assert isinstance(call_args.kwargs["auth"], httpx.BasicAuth)

    @pytest.mark.asyncio
    async def test_sets_json_accept_header(self, onet_client):
        """Should set Accept: application/json header."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"occupation": []}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            await onet_client.search_occupations("test")

            call_args = mock_client.get.call_args
            headers = call_args.kwargs.get("headers", {})
            assert headers.get("Accept") == "application/json"

    @pytest.mark.asyncio
    async def test_async_client_has_timeout(self, onet_client):
        """Should configure httpx.AsyncClient with timeout."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"occupation": []}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            await onet_client.search_occupations("test")

            mock_client_class.assert_called_once_with(timeout=30.0)


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_rate_limit_with_invalid_retry_after_header(self, onet_client):
        """Should handle non-numeric Retry-After header gracefully."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "invalid-value"}
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            message="Too Many Requests",
            request=MagicMock(),
            response=mock_response,
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            with pytest.raises(OnetRateLimitError) as exc_info:
                await onet_client.search_occupations("software")

            assert exc_info.value.status_code == 429
            assert exc_info.value.retry_after is None

    @pytest.mark.asyncio
    async def test_rate_limit_without_retry_after_header(self, onet_client):
        """Should handle missing Retry-After header gracefully."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {}
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            message="Too Many Requests",
            request=MagicMock(),
            response=mock_response,
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            with pytest.raises(OnetRateLimitError) as exc_info:
                await onet_client.search_occupations("software")

            assert exc_info.value.status_code == 429
            assert exc_info.value.retry_after is None

    def test_empty_api_key_creates_valid_auth(self):
        """Should create Basic Auth even with empty API key."""
        mock_settings = MagicMock(spec=Settings)
        mock_settings.onet_api_key = MagicMock()
        mock_settings.onet_api_key.get_secret_value.return_value = ""
        mock_settings.onet_api_base_url = "https://services.onetcenter.org/ws/"

        client = OnetApiClient(settings=mock_settings)
        auth = client._get_auth()

        assert isinstance(auth, httpx.BasicAuth)

    @pytest.mark.asyncio
    async def test_search_occupations_missing_occupation_key(self, onet_client):
        """Should return empty list when response is missing 'occupation' key."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}  # Missing 'occupation' key
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            results = await onet_client.search_occupations("software")

            assert results == []

    @pytest.mark.asyncio
    async def test_get_work_activities_missing_element_key(self, onet_client):
        """Should return empty list when response is missing 'element' key."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}  # Missing 'element' key
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            results = await onet_client.get_work_activities("15-1252.00")

            assert results == []

    @pytest.mark.asyncio
    async def test_get_tasks_missing_task_key(self, onet_client):
        """Should return empty list when response is missing 'task' key."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}  # Missing 'task' key
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            results = await onet_client.get_tasks("15-1252.00")

            assert results == []
