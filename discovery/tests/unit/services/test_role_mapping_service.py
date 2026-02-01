"""Unit tests for role mapping and O*NET services.

Tests the OnetService class that wraps OnetApiClient, following TDD methodology.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.config import Settings
from app.services.onet_client import OnetApiClient
from app.services.role_mapping_service import (
    OnetService,
    RoleMappingService,
    get_onet_service,
    get_role_mapping_service,
)


@pytest.fixture
def mock_onet_client():
    """Create a mock OnetApiClient for testing."""
    client = MagicMock(spec=OnetApiClient)
    client.search_occupations = AsyncMock()
    client.get_occupation = AsyncMock()
    return client


@pytest.fixture
def onet_service(mock_onet_client):
    """Create an OnetService instance with mocked client."""
    return OnetService(client=mock_onet_client)


class TestOnetServiceInit:
    """Tests for OnetService initialization."""

    def test_init_accepts_onet_api_client(self, mock_onet_client):
        """OnetService should accept OnetApiClient as dependency."""
        service = OnetService(client=mock_onet_client)
        assert service.client is mock_onet_client

    def test_init_stores_client_reference(self, mock_onet_client):
        """OnetService should store client for later use."""
        service = OnetService(client=mock_onet_client)
        assert hasattr(service, "client")
        assert service.client == mock_onet_client


class TestOnetServiceSearch:
    """Tests for OnetService.search method."""

    @pytest.mark.asyncio
    async def test_search_calls_client_search_occupations(self, onet_service, mock_onet_client):
        """OnetService.search should delegate to client.search_occupations."""
        mock_onet_client.search_occupations.return_value = []

        await onet_service.search("software developer")

        mock_onet_client.search_occupations.assert_called_once_with("software developer")

    @pytest.mark.asyncio
    async def test_search_returns_client_results(self, onet_service, mock_onet_client):
        """OnetService.search should return results from client."""
        expected_results = [
            {"code": "15-1252.00", "title": "Software Developers"},
            {"code": "15-1251.00", "title": "Computer Programmers"},
        ]
        mock_onet_client.search_occupations.return_value = expected_results

        results = await onet_service.search("software")

        assert results == expected_results

    @pytest.mark.asyncio
    async def test_search_returns_empty_list_when_no_matches(self, onet_service, mock_onet_client):
        """OnetService.search should return empty list when client returns none."""
        mock_onet_client.search_occupations.return_value = []

        results = await onet_service.search("nonexistent occupation")

        assert results == []

    @pytest.mark.asyncio
    async def test_search_returns_list_type(self, onet_service, mock_onet_client):
        """OnetService.search should always return a list."""
        mock_onet_client.search_occupations.return_value = [
            {"code": "15-1252.00", "title": "Software Developers"}
        ]

        results = await onet_service.search("software")

        assert isinstance(results, list)


class TestOnetServiceGetOccupation:
    """Tests for OnetService.get_occupation method."""

    @pytest.mark.asyncio
    async def test_get_occupation_calls_client(self, onet_service, mock_onet_client):
        """OnetService.get_occupation should delegate to client.get_occupation."""
        mock_onet_client.get_occupation.return_value = None

        await onet_service.get_occupation("15-1252.00")

        mock_onet_client.get_occupation.assert_called_once_with("15-1252.00")

    @pytest.mark.asyncio
    async def test_get_occupation_returns_occupation_details(self, onet_service, mock_onet_client):
        """OnetService.get_occupation should return occupation details from client."""
        expected_occupation = {
            "code": "15-1252.00",
            "title": "Software Developers",
            "description": "Research, design, and develop computer software.",
        }
        mock_onet_client.get_occupation.return_value = expected_occupation

        result = await onet_service.get_occupation("15-1252.00")

        assert result == expected_occupation

    @pytest.mark.asyncio
    async def test_get_occupation_returns_none_when_not_found(self, onet_service, mock_onet_client):
        """OnetService.get_occupation should return None when occupation not found."""
        mock_onet_client.get_occupation.return_value = None

        result = await onet_service.get_occupation("00-0000.00")

        assert result is None


class TestGetOnetServiceDependency:
    """Tests for get_onet_service dependency function."""

    def test_get_onet_service_returns_onet_service(self):
        """get_onet_service should return an OnetService instance."""
        with patch("app.services.role_mapping_service.get_settings") as mock_get_settings:
            mock_settings = MagicMock(spec=Settings)
            mock_settings.onet_api_key = MagicMock()
            mock_settings.onet_api_key.get_secret_value.return_value = "test_key"
            mock_settings.onet_api_base_url = "https://services.onetcenter.org/ws/"
            mock_get_settings.return_value = mock_settings

            service = get_onet_service()

            assert isinstance(service, OnetService)

    def test_get_onet_service_creates_client(self):
        """get_onet_service should create OnetApiClient with settings."""
        with patch("app.services.role_mapping_service.get_settings") as mock_get_settings:
            with patch("app.services.role_mapping_service.OnetApiClient") as mock_client_class:
                mock_settings = MagicMock(spec=Settings)
                mock_settings.onet_api_key = MagicMock()
                mock_settings.onet_api_key.get_secret_value.return_value = "test_key"
                mock_settings.onet_api_base_url = "https://services.onetcenter.org/ws/"
                mock_get_settings.return_value = mock_settings
                mock_client_class.return_value = MagicMock(spec=OnetApiClient)

                get_onet_service()

                mock_client_class.assert_called_once_with(settings=mock_settings)

    def test_get_onet_service_injects_client_into_service(self):
        """get_onet_service should inject the created client into OnetService."""
        with patch("app.services.role_mapping_service.get_settings") as mock_get_settings:
            with patch("app.services.role_mapping_service.OnetApiClient") as mock_client_class:
                mock_settings = MagicMock(spec=Settings)
                mock_settings.onet_api_key = MagicMock()
                mock_settings.onet_api_key.get_secret_value.return_value = "test_key"
                mock_settings.onet_api_base_url = "https://services.onetcenter.org/ws/"
                mock_get_settings.return_value = mock_settings
                mock_client = MagicMock(spec=OnetApiClient)
                mock_client_class.return_value = mock_client

                service = get_onet_service()

                assert service.client is mock_client


class TestRoleMappingService:
    """Tests for RoleMappingService (placeholder tests)."""

    def test_get_role_mapping_service_returns_instance(self):
        """get_role_mapping_service should return RoleMappingService instance."""
        service = get_role_mapping_service()
        assert isinstance(service, RoleMappingService)

    @pytest.mark.asyncio
    async def test_get_by_session_id_raises_not_implemented(self):
        """RoleMappingService.get_by_session_id should raise NotImplementedError."""
        service = RoleMappingService()
        from uuid import uuid4

        with pytest.raises(NotImplementedError):
            await service.get_by_session_id(uuid4())

    @pytest.mark.asyncio
    async def test_update_raises_not_implemented(self):
        """RoleMappingService.update should raise NotImplementedError."""
        service = RoleMappingService()
        from uuid import uuid4

        with pytest.raises(NotImplementedError):
            await service.update(uuid4())

    @pytest.mark.asyncio
    async def test_bulk_confirm_raises_not_implemented(self):
        """RoleMappingService.bulk_confirm should raise NotImplementedError."""
        service = RoleMappingService()
        from uuid import uuid4

        with pytest.raises(NotImplementedError):
            await service.bulk_confirm(uuid4(), 0.8)
