"""LOB to NAICS mapping service."""
import json
from dataclasses import dataclass
from typing import Any

from app.repositories.lob_mapping_repository import LobMappingRepository


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
    ):
        """Initialize service with repository and optional LLM.

        Args:
            repository: LobMappingRepository for database operations.
            llm_service: Optional LLM service for fallback mapping.
        """
        self.repository = repository
        self.llm = llm_service

    async def map_lob_to_naics(self, lob: str) -> LobNaicsResult:
        """Map LOB string to NAICS codes.

        1. Normalize input (lowercase, trim)
        2. Check curated lookup table (exact match)
        3. Try fuzzy match
        4. Fall back to LLM if no match
        5. Cache LLM results for future use

        Args:
            lob: Line of Business string to map.

        Returns:
            LobNaicsResult with NAICS codes and metadata.
        """
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

        # Try fuzzy match
        mapping = await self.repository.find_fuzzy(normalized, threshold=0.85)
        if mapping:
            return LobNaicsResult(
                lob=lob,
                naics_codes=mapping.naics_codes,
                confidence=mapping.confidence * 0.9,  # Reduce for fuzzy
                source="fuzzy",
            )

        # LLM fallback
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

    async def _llm_map(self, lob: str) -> list[str] | None:
        """Use LLM to determine NAICS codes for LOB.

        Args:
            lob: Line of Business string.

        Returns:
            List of NAICS codes if successful, None otherwise.
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
            codes = json.loads(response.strip())
            if isinstance(codes, list) and all(isinstance(c, str) for c in codes):
                return codes
        except (json.JSONDecodeError, Exception):
            pass

        return None
