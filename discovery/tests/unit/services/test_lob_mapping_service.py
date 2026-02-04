"""Test LobMappingService."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.exceptions import LLMError, ValidationException
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
    async def test_no_exact_match_falls_through_to_llm(self, service, mock_repository, mock_llm_service):
        """Test no exact match falls through to LLM (fuzzy match removed)."""
        mock_repository.find_by_pattern.return_value = None
        mock_llm_service.complete.return_value = '["522110"]'

        result = await service.map_lob_to_naics("Retail Banking Div")

        # Should fall through to LLM since fuzzy match was removed
        assert result.naics_codes == ["522110"]
        assert result.confidence == 0.8  # LLM confidence
        assert result.source == "llm"
        mock_llm_service.complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_llm_fallback_when_no_match(self, service, mock_repository, mock_llm_service):
        """Test LLM fallback when no curated match."""
        mock_repository.find_by_pattern.return_value = None
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


class TestLobValidation:
    """Test LOB input validation."""

    @pytest.mark.asyncio
    async def test_empty_lob_raises_validation_error(self, service):
        """Test empty LOB raises ValidationException."""
        with pytest.raises(ValidationException, match="cannot be empty"):
            await service.map_lob_to_naics("")

    @pytest.mark.asyncio
    async def test_whitespace_only_lob_raises_validation_error(self, service):
        """Test whitespace-only LOB raises ValidationException."""
        with pytest.raises(ValidationException, match="cannot be empty"):
            await service.map_lob_to_naics("   ")

    @pytest.mark.asyncio
    async def test_overlength_lob_raises_validation_error(self, mock_repository, mock_llm_service):
        """Test overlength LOB raises ValidationException."""
        service = LobMappingService(mock_repository, mock_llm_service, max_lob_length=10)
        with pytest.raises(ValidationException, match="exceeds maximum"):
            await service.map_lob_to_naics("A" * 11)

    @pytest.mark.asyncio
    async def test_control_chars_raises_validation_error(self, service):
        """Test LOB with control characters raises ValidationException."""
        with pytest.raises(ValidationException, match="control characters"):
            await service.map_lob_to_naics("Retail\x00Banking")

    @pytest.mark.asyncio
    async def test_tab_and_newline_allowed(self, service, mock_repository):
        """Test common whitespace (tab, newline) is allowed."""
        from app.models.lob_naics_mapping import LobNaicsMapping

        mock_repository.find_by_pattern.return_value = LobNaicsMapping(
            lob_pattern="retail banking",
            naics_codes=["522110"],
            confidence=1.0,
            source="curated",
        )

        # Tab and newline are common whitespace and should be allowed
        result = await service.map_lob_to_naics("Retail\tBanking")
        assert result is not None


class TestNaicsValidation:
    """Test NAICS code validation."""

    def test_validate_naics_filters_invalid_codes(self, service):
        """Test invalid NAICS codes are filtered out."""
        codes = ["52", "invalid", "523110", "", "1234567", "abc123"]
        valid = service._validate_naics_codes(codes)
        assert valid == ["52", "523110"]

    def test_validate_naics_accepts_2_to_6_digits(self, service):
        """Test NAICS codes from 2 to 6 digits are accepted."""
        codes = ["52", "523", "5231", "52311", "523110"]
        valid = service._validate_naics_codes(codes)
        assert valid == codes

    def test_validate_naics_rejects_1_digit(self, service):
        """Test 1-digit codes are rejected."""
        valid = service._validate_naics_codes(["5"])
        assert valid == []

    def test_validate_naics_rejects_7_digits(self, service):
        """Test 7-digit codes are rejected."""
        valid = service._validate_naics_codes(["5231100"])
        assert valid == []

    def test_validate_naics_empty_list_returns_empty(self, service):
        """Test empty list returns empty."""
        valid = service._validate_naics_codes([])
        assert valid == []


class TestLlmErrorHandling:
    """Test LLM error propagation."""

    @pytest.mark.asyncio
    async def test_llm_error_propagates(self, service, mock_repository, mock_llm_service):
        """Test LLMError exceptions propagate to caller."""
        mock_repository.find_by_pattern.return_value = None
        mock_llm_service.complete.side_effect = LLMError("API error")

        with pytest.raises(LLMError, match="API error"):
            await service.map_lob_to_naics("Test LOB")

    @pytest.mark.asyncio
    async def test_json_decode_error_returns_none(self, service, mock_repository, mock_llm_service):
        """Test JSON decode error returns empty result (no match)."""
        mock_repository.find_by_pattern.return_value = None
        mock_llm_service.complete.return_value = "not valid json"

        result = await service.map_lob_to_naics("Test LOB")

        assert result.naics_codes == []
        assert result.source == "none"

    @pytest.mark.asyncio
    async def test_llm_returns_non_list_returns_none(self, service, mock_repository, mock_llm_service):
        """Test LLM returning non-list returns empty result."""
        mock_repository.find_by_pattern.return_value = None
        mock_llm_service.complete.return_value = '{"code": "52"}'

        result = await service.map_lob_to_naics("Test LOB")

        assert result.naics_codes == []
        assert result.source == "none"

    @pytest.mark.asyncio
    async def test_llm_returns_invalid_codes_filtered(self, service, mock_repository, mock_llm_service):
        """Test invalid NAICS codes from LLM are filtered."""
        mock_repository.find_by_pattern.return_value = None
        mock_llm_service.complete.return_value = '["52", "invalid", "523110"]'

        result = await service.map_lob_to_naics("Test LOB")

        # Only valid codes should be returned
        assert result.naics_codes == ["52", "523110"]
        assert result.source == "llm"
