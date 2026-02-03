"""Unit tests for role mapping and O*NET services.

Tests the OnetService class that uses the local O*NET repository.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.role_mapping_service import (
    OnetService,
    RoleMappingService,
    get_onet_service,
    get_role_mapping_service,
)


@pytest.fixture
def mock_onet_repository():
    """Create a mock OnetRepository for testing."""
    from app.repositories.onet_repository import OnetRepository

    repo = MagicMock(spec=OnetRepository)
    repo.search_with_full_text = AsyncMock()
    repo.get_by_code = AsyncMock()
    return repo


@pytest.fixture
def onet_service(mock_onet_repository):
    """Create an OnetService instance with mocked repository."""
    return OnetService(repository=mock_onet_repository)


class TestOnetServiceInit:
    """Tests for OnetService initialization."""

    def test_init_accepts_onet_repository(self, mock_onet_repository):
        """OnetService should accept OnetRepository as dependency."""
        service = OnetService(repository=mock_onet_repository)
        assert service.repository is mock_onet_repository

    def test_init_stores_repository_reference(self, mock_onet_repository):
        """OnetService should store repository for later use."""
        service = OnetService(repository=mock_onet_repository)
        assert hasattr(service, "repository")
        assert service.repository == mock_onet_repository


class TestOnetServiceSearch:
    """Tests for OnetService.search method."""

    @pytest.mark.asyncio
    async def test_search_calls_repository_search(self, onet_service, mock_onet_repository):
        """OnetService.search should delegate to repository.search_with_full_text."""
        mock_onet_repository.search_with_full_text.return_value = []

        await onet_service.search("software developer")

        mock_onet_repository.search_with_full_text.assert_called_once_with("software developer")

    @pytest.mark.asyncio
    async def test_search_returns_formatted_results(self, onet_service, mock_onet_repository):
        """OnetService.search should return formatted results from repository."""
        mock_occupation = MagicMock(
            code="15-1252.00",
            title="Software Developers",
        )
        mock_onet_repository.search_with_full_text.return_value = [mock_occupation]

        results = await onet_service.search("software")

        assert len(results) == 1
        assert results[0]["code"] == "15-1252.00"
        assert results[0]["title"] == "Software Developers"
        assert results[0]["score"] == 1.0

    @pytest.mark.asyncio
    async def test_search_returns_empty_list_when_no_matches(self, onet_service, mock_onet_repository):
        """OnetService.search should return empty list when repository returns none."""
        mock_onet_repository.search_with_full_text.return_value = []

        results = await onet_service.search("nonexistent occupation")

        assert results == []

    @pytest.mark.asyncio
    async def test_search_returns_list_type(self, onet_service, mock_onet_repository):
        """OnetService.search should always return a list."""
        mock_occupation = MagicMock(
            code="15-1252.00",
            title="Software Developers",
        )
        mock_onet_repository.search_with_full_text.return_value = [mock_occupation]

        results = await onet_service.search("software")

        assert isinstance(results, list)


class TestOnetServiceGetOccupation:
    """Tests for OnetService.get_occupation method."""

    @pytest.mark.asyncio
    async def test_get_occupation_calls_repository(self, onet_service, mock_onet_repository):
        """OnetService.get_occupation should delegate to repository.get_by_code."""
        mock_onet_repository.get_by_code.return_value = None

        await onet_service.get_occupation("15-1252.00")

        mock_onet_repository.get_by_code.assert_called_once_with("15-1252.00")

    @pytest.mark.asyncio
    async def test_get_occupation_returns_occupation_details(self, onet_service, mock_onet_repository):
        """OnetService.get_occupation should return occupation details from repository."""
        mock_occupation = MagicMock(
            code="15-1252.00",
            title="Software Developers",
            description="Research, design, and develop computer software.",
        )
        mock_onet_repository.get_by_code.return_value = mock_occupation

        result = await onet_service.get_occupation("15-1252.00")

        assert result["code"] == "15-1252.00"
        assert result["title"] == "Software Developers"
        assert result["description"] == "Research, design, and develop computer software."

    @pytest.mark.asyncio
    async def test_get_occupation_returns_none_when_not_found(self, onet_service, mock_onet_repository):
        """OnetService.get_occupation should return None when occupation not found."""
        mock_onet_repository.get_by_code.return_value = None

        result = await onet_service.get_occupation("00-0000.00")

        assert result is None


class TestGetOnetServiceDependency:
    """Tests for get_onet_service dependency function."""

    def test_get_onet_service_is_async_generator(self):
        """get_onet_service should be an async generator function."""
        import inspect

        assert inspect.isasyncgenfunction(get_onet_service)


class TestRoleMappingServiceDependency:
    """Tests for get_role_mapping_service dependency function."""

    def test_get_role_mapping_service_is_async_generator(self):
        """get_role_mapping_service should be an async generator function."""
        import inspect

        assert inspect.isasyncgenfunction(get_role_mapping_service)


class TestRoleMappingServiceInit:
    """Tests for RoleMappingService initialization."""

    def test_init_requires_repository_and_agent(self):
        """RoleMappingService should require repository and agent."""
        mock_repo = MagicMock()
        mock_agent = MagicMock()

        service = RoleMappingService(
            repository=mock_repo,
            role_mapping_agent=mock_agent,
        )

        assert service.repository is mock_repo
        assert service.role_mapping_agent is mock_agent

    def test_init_accepts_optional_upload_service(self):
        """RoleMappingService should accept optional upload_service."""
        mock_repo = MagicMock()
        mock_agent = MagicMock()
        mock_upload_service = MagicMock()

        service = RoleMappingService(
            repository=mock_repo,
            role_mapping_agent=mock_agent,
            upload_service=mock_upload_service,
        )

        assert service.upload_service is mock_upload_service
