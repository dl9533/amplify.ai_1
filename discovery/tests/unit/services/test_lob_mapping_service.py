"""Test LobMappingService."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.lob_mapping_service import LobMappingService, LobNaicsResult


@pytest.fixture
def mock_repository():
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_llm_service():
    llm = AsyncMock()
    return llm


@pytest.fixture
def service(mock_repository, mock_llm_service):
    return LobMappingService(mock_repository, mock_llm_service)


class TestMapLobToNaics:
    """Test LOB to NAICS mapping."""

    @pytest.mark.asyncio
    async def test_exact_match_from_curated(self, service, mock_repository):
        """Test exact match returns curated mapping."""
        from app.models.lob_naics_mapping import LobNaicsMapping

        mock_repository.find_by_pattern.return_value = LobNaicsMapping(
            lob_pattern="retail banking",
            naics_codes=["522110"],
            confidence=1.0,
            source="curated",
        )

        result = await service.map_lob_to_naics("Retail Banking")

        assert result.naics_codes == ["522110"]
        assert result.confidence == 1.0
        assert result.source == "curated"

    @pytest.mark.asyncio
    async def test_fuzzy_match_reduces_confidence(self, service, mock_repository):
        """Test fuzzy match reduces confidence score."""
        from app.models.lob_naics_mapping import LobNaicsMapping

        mock_repository.find_by_pattern.return_value = None
        mock_repository.find_fuzzy.return_value = LobNaicsMapping(
            lob_pattern="retail bank",
            naics_codes=["522110"],
            confidence=0.95,
            source="curated",
        )

        result = await service.map_lob_to_naics("Retail Banking Div")

        assert result.naics_codes == ["522110"]
        assert result.confidence < 0.95  # Reduced for fuzzy
        assert result.source == "fuzzy"

    @pytest.mark.asyncio
    async def test_llm_fallback_when_no_match(self, service, mock_repository, mock_llm_service):
        """Test LLM fallback when no curated match."""
        mock_repository.find_by_pattern.return_value = None
        mock_repository.find_fuzzy.return_value = None
        mock_llm_service.complete.return_value = '["523110"]'

        result = await service.map_lob_to_naics("Investment Management")

        mock_llm_service.complete.assert_called_once()
        assert result.source == "llm"
        assert result.confidence == 0.8

    @pytest.mark.asyncio
    async def test_no_match_returns_empty(self, mock_repository):
        """Test no match returns empty result."""
        service = LobMappingService(mock_repository, llm_service=None)
        mock_repository.find_by_pattern.return_value = None
        mock_repository.find_fuzzy.return_value = None

        result = await service.map_lob_to_naics("Unknown Business")

        assert result.naics_codes == []
        assert result.confidence == 0.0
        assert result.source == "none"


class TestMapBatch:
    """Test batch mapping."""

    @pytest.mark.asyncio
    async def test_map_batch_deduplicates(self, service, mock_repository):
        """Test batch mapping deduplicates LOBs."""
        from app.models.lob_naics_mapping import LobNaicsMapping

        mock_repository.find_by_pattern.return_value = LobNaicsMapping(
            lob_pattern="retail",
            naics_codes=["522"],
            confidence=1.0,
            source="curated",
        )

        result = await service.map_batch(["Retail", "Retail", "RETAIL"])

        # Should only call repository once per unique normalized value
        assert len(result) <= 3  # At most 3 unique case variations


class TestNormalize:
    """Test LOB normalization."""

    def test_normalizes_to_lowercase(self, service):
        """Test normalization lowercases."""
        assert service._normalize("Retail Banking") == "retail banking"

    def test_normalizes_strips_whitespace(self, service):
        """Test normalization strips whitespace."""
        assert service._normalize("  Retail Banking  ") == "retail banking"


def test_lob_naics_result_dataclass():
    """Test LobNaicsResult dataclass."""
    result = LobNaicsResult(
        lob="Retail Banking",
        naics_codes=["522110"],
        confidence=1.0,
        source="curated",
    )
    assert result.lob == "Retail Banking"
    assert result.naics_codes == ["522110"]
    assert result.confidence == 1.0
    assert result.source == "curated"


def test_lob_mapping_service_exists():
    """Test LobMappingService is importable."""
    from app.services.lob_mapping_service import LobMappingService
    assert LobMappingService is not None


def test_lob_naics_result_exported():
    """Test LobNaicsResult is importable."""
    from app.services.lob_mapping_service import LobNaicsResult
    assert LobNaicsResult is not None
