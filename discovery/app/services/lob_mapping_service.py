"""LOB to NAICS mapping service."""
import json
import logging
import re
from dataclasses import dataclass
from typing import Any

from app.exceptions import LLMError, ValidationException
from app.repositories.lob_mapping_repository import LobMappingRepository

logger = logging.getLogger(__name__)

# NAICS code pattern: 2-6 digit numeric codes
NAICS_CODE_PATTERN = re.compile(r"^\d{2,6}$")

# Maximum LOB pattern length
MAX_LOB_PATTERN_LENGTH = 255


@dataclass
class LobNaicsResult:
    """Result of LOB to NAICS mapping."""

    lob: str
    naics_codes: list[str]
    confidence: float
    source: str  # "curated", "fuzzy", or "llm"


class LobMappingService:
    """Map Line of Business values to NAICS industry codes."""

    def __init__(
        self,
        repository: LobMappingRepository,
        llm_service: Any = None,
        max_lob_length: int = MAX_LOB_PATTERN_LENGTH,
    ):
        """Initialize service with repository and optional LLM.

        Args:
            repository: LobMappingRepository for database operations.
            llm_service: Optional LLM service for fallback mapping.
            max_lob_length: Maximum allowed LOB pattern length.
        """
        self.repository = repository
        self.llm = llm_service
        self.max_lob_length = max_lob_length

    async def map_lob_to_naics(self, lob: str) -> LobNaicsResult:
        """Map LOB string to NAICS codes.

        1. Validate and normalize input
        2. Check curated lookup table (exact match)
        3. Fall back to LLM if no match
        4. Cache LLM results for future use

        Args:
            lob: Line of Business string to map.

        Returns:
            LobNaicsResult with NAICS codes and metadata.

        Raises:
            ValidationException: If LOB pattern is invalid (too long, contains control chars).
        """
        # Validate input
        self._validate_lob_input(lob)
        normalized = self._normalize(lob)

        # Try exact match first
        mapping = await self.repository.find_by_pattern(normalized)
        if mapping:
            return LobNaicsResult(
                lob=lob,
                naics_codes=mapping.naics_codes,
                confidence=mapping.confidence,
                source=mapping.source,
            )

        # LLM fallback (fuzzy match removed - requires pg_trgm extension)
        if self.llm:
            naics_codes = await self._llm_map(lob)
            if naics_codes:
                # Cache the result
                await self.repository.create(
                    lob_pattern=normalized,
                    naics_codes=naics_codes,
                    confidence=0.8,
                    source="llm",
                )
                return LobNaicsResult(
                    lob=lob,
                    naics_codes=naics_codes,
                    confidence=0.8,
                    source="llm",
                )

        # No match found
        return LobNaicsResult(
            lob=lob,
            naics_codes=[],
            confidence=0.0,
            source="none",
        )

    async def map_batch(self, lobs: list[str]) -> dict[str, LobNaicsResult]:
        """Map multiple LOBs to NAICS codes.

        Args:
            lobs: List of LOB strings to map.

        Returns:
            Dict mapping LOB string to LobNaicsResult.
        """
        results = {}
        for lob in set(lobs):  # Dedupe
            results[lob] = await self.map_lob_to_naics(lob)
        return results

    def _normalize(self, lob: str) -> str:
        """Normalize LOB string for matching.

        Args:
            lob: Raw LOB string.

        Returns:
            Normalized lowercase trimmed string.
        """
        return lob.lower().strip()

    def _validate_lob_input(self, lob: str) -> None:
        """Validate LOB input string.

        Args:
            lob: LOB string to validate.

        Raises:
            ValidationException: If input is invalid.
        """
        if not lob or not lob.strip():
            raise ValidationException(
                "LOB pattern cannot be empty",
                details={"lob": lob},
            )

        if len(lob) > self.max_lob_length:
            raise ValidationException(
                f"LOB pattern exceeds maximum length of {self.max_lob_length} characters",
                details={"lob_length": len(lob), "max_length": self.max_lob_length},
            )

        # Check for control characters (except common whitespace)
        if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", lob):
            raise ValidationException(
                "LOB pattern contains invalid control characters",
                details={"lob": lob[:50]},  # Truncate for safety
            )

    def _validate_naics_codes(self, codes: list[str]) -> list[str]:
        """Validate and filter NAICS codes.

        Args:
            codes: List of potential NAICS codes.

        Returns:
            List of valid NAICS codes only.
        """
        valid_codes = []
        for code in codes:
            if NAICS_CODE_PATTERN.match(code):
                valid_codes.append(code)
            else:
                logger.warning("Invalid NAICS code format from LLM: %s", code)
        return valid_codes

    async def _llm_map(self, lob: str) -> list[str] | None:
        """Use LLM to determine NAICS codes for LOB.

        Args:
            lob: Line of Business string.

        Returns:
            List of valid NAICS codes if successful, None otherwise.

        Raises:
            LLMError: If there's an LLM service error (auth, rate limit, connection).
        """
        if not self.llm:
            return None

        prompt = f"""Map this Line of Business to NAICS industry codes.

Line of Business: "{lob}"

Return a JSON array of the most relevant 2-digit or 3-digit NAICS codes.
Common examples:
- "Retail Banking" → ["522110"]
- "Software Development" → ["541511"]
- "Healthcare" → ["62"]

Respond with ONLY a JSON array like ["52", "523110"]. No explanation."""

        try:
            response = await self.llm.complete(prompt)
        except LLMError:
            # Let LLM service errors propagate (auth, rate limit, connection issues)
            raise
        except Exception as e:
            # Log unexpected errors from LLM service
            logger.error("Unexpected error calling LLM service: %s", e)
            return None

        # Parse JSON response
        try:
            codes = json.loads(response.strip())
        except json.JSONDecodeError as e:
            logger.warning("Failed to parse LLM response as JSON: %s", e)
            logger.debug("LLM response was: %s", response[:200])
            return None

        # Validate response structure
        if not isinstance(codes, list):
            logger.warning("LLM response is not a list: %s", type(codes))
            return None

        if not all(isinstance(c, str) for c in codes):
            logger.warning("LLM response contains non-string elements")
            return None

        # Validate NAICS code format
        valid_codes = self._validate_naics_codes(codes)
        if not valid_codes:
            logger.warning("No valid NAICS codes in LLM response: %s", codes)
            return None

        return valid_codes
