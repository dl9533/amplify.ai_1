"""Test LOB mapping lookup endpoint."""
import pytest
from unittest.mock import AsyncMock
from uuid import uuid4


class TestLobMappingLookupSchemas:
    """Test schemas for LOB mapping lookup."""

    def test_lob_naics_lookup_response_exists(self):
        """Test LobNaicsLookupResponse schema is defined."""
        from app.schemas.lob_mapping import LobNaicsLookupResponse

        assert LobNaicsLookupResponse is not None

    def test_lob_naics_lookup_response_fields(self):
        """Test LobNaicsLookupResponse has expected fields."""
        from app.schemas.lob_mapping import LobNaicsLookupResponse

        response = LobNaicsLookupResponse(
            lob="Investment Banking",
            naics_codes=["523110", "523130"],
            confidence=0.95,
            source="curated",
        )

        assert response.lob == "Investment Banking"
        assert response.naics_codes == ["523110", "523130"]
        assert response.confidence == 0.95
        assert response.source == "curated"


class TestLobMappingRouter:
    """Test LOB mapping router."""

    def test_lob_mapping_router_exists(self):
        """Test LOB mapping router is defined."""
        from app.routers.lob_mappings import router

        assert router is not None

    def test_lookup_lob_endpoint_exists(self):
        """Test lookup_lob endpoint is defined."""
        from app.routers.lob_mappings import lookup_lob

        assert lookup_lob is not None
        assert callable(lookup_lob)


class TestLobMappingLookupEndpoint:
    """Test LOB mapping lookup endpoint."""

    @pytest.mark.asyncio
    async def test_lookup_lob_returns_response(self):
        """Test endpoint returns LobNaicsLookupResponse."""
        from app.routers.lob_mappings import lookup_lob
        from app.schemas.lob_mapping import LobNaicsLookupResponse
        from app.services.lob_mapping_service import LobNaicsResult

        # Create mock service
        mock_service = AsyncMock()
        mock_service.map_lob_to_naics.return_value = LobNaicsResult(
            lob="Technology",
            naics_codes=["541511", "541512"],
            confidence=0.92,
            source="curated",
        )

        result = await lookup_lob(
            lob="Technology",
            service=mock_service,
        )

        assert isinstance(result, LobNaicsLookupResponse)
        assert result.lob == "Technology"
        assert result.naics_codes == ["541511", "541512"]
        assert result.confidence == 0.92
        assert result.source == "curated"

    @pytest.mark.asyncio
    async def test_lookup_lob_calls_service(self):
        """Test endpoint calls service with correct LOB."""
        from app.routers.lob_mappings import lookup_lob
        from app.services.lob_mapping_service import LobNaicsResult

        mock_service = AsyncMock()
        mock_service.map_lob_to_naics.return_value = LobNaicsResult(
            lob="Healthcare",
            naics_codes=["621111"],
            confidence=0.85,
            source="fuzzy",
        )

        await lookup_lob(
            lob="Healthcare",
            service=mock_service,
        )

        mock_service.map_lob_to_naics.assert_called_once_with("Healthcare")
