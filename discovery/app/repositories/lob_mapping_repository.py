"""Repository for LOB to NAICS mappings."""
import logging

from sqlalchemy import select, func
from sqlalchemy.exc import ProgrammingError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lob_naics_mapping import LobNaicsMapping

logger = logging.getLogger(__name__)


class LobMappingRepository:
    """Repository for LOB-NAICS mapping operations.

    Provides data access methods for the lob_naics_mappings table,
    supporting exact and fuzzy pattern matching.
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: Async SQLAlchemy session.
        """
        self.session = session

    async def find_by_pattern(self, pattern: str) -> LobNaicsMapping | None:
        """Find mapping by exact pattern match (case-insensitive).

        Args:
            pattern: LOB pattern to search for.

        Returns:
            LobNaicsMapping if found, None otherwise.
        """
        normalized = pattern.lower().strip()
        stmt = select(LobNaicsMapping).where(
            func.lower(LobNaicsMapping.lob_pattern) == normalized
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_fuzzy(
        self,
        pattern: str,
        threshold: float = 0.85,
    ) -> LobNaicsMapping | None:
        """Find mapping using fuzzy matching.

        Uses PostgreSQL pg_trgm similarity function for fuzzy matching.
        Returns best match above threshold.

        Note: Requires pg_trgm extension. If not available, falls back to
        exact match after rolling back the failed transaction.

        Args:
            pattern: LOB pattern to search for.
            threshold: Minimum similarity score (0-1).

        Returns:
            Best matching LobNaicsMapping above threshold, or None.
        """
        normalized = pattern.lower().strip()

        # Use pg_trgm similarity if available
        stmt = (
            select(LobNaicsMapping)
            .where(func.similarity(LobNaicsMapping.lob_pattern, normalized) >= threshold)
            .order_by(func.similarity(LobNaicsMapping.lob_pattern, normalized).desc())
            .limit(1)
        )

        try:
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except (ProgrammingError, OperationalError) as e:
            # pg_trgm extension not available - rollback and fall back to exact match
            logger.warning(
                "pg_trgm fuzzy match failed, falling back to exact match: %s",
                e,
                extra={"pattern": normalized, "error": str(e)},
            )
            await self.session.rollback()
            return await self.find_by_pattern(pattern)

    async def create(
        self,
        lob_pattern: str,
        naics_codes: list[str],
        confidence: float = 1.0,
        source: str = "curated",
    ) -> LobNaicsMapping:
        """Create a new LOB mapping.

        Args:
            lob_pattern: The LOB pattern (will be normalized to lowercase).
            naics_codes: List of NAICS codes.
            confidence: Confidence score (0-1).
            source: Source of the mapping (curated, llm, fuzzy).

        Returns:
            Created LobNaicsMapping instance.
        """
        mapping = LobNaicsMapping(
            lob_pattern=lob_pattern.lower().strip(),
            naics_codes=naics_codes,
            confidence=confidence,
            source=source,
        )
        self.session.add(mapping)
        await self.session.flush()
        return mapping

    async def get_all(self) -> list[LobNaicsMapping]:
        """Get all LOB mappings ordered by pattern.

        Returns:
            List of all LobNaicsMapping records.
        """
        stmt = select(LobNaicsMapping).order_by(LobNaicsMapping.lob_pattern)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def bulk_upsert(
        self,
        mappings: list[dict],
    ) -> int:
        """Bulk upsert LOB mappings.

        For each mapping dict, updates existing record if pattern exists,
        otherwise creates new record.

        Args:
            mappings: List of dicts with lob_pattern, naics_codes, etc.

        Returns:
            Number of mappings processed.
        """
        count = 0
        for data in mappings:
            existing = await self.find_by_pattern(data["lob_pattern"])
            if existing:
                existing.naics_codes = data["naics_codes"]
                existing.confidence = data.get("confidence", 1.0)
                existing.source = data.get("source", "curated")
            else:
                await self.create(**data)
            count += 1
        return count

    async def delete_by_pattern(self, pattern: str) -> bool:
        """Delete a mapping by pattern.

        Args:
            pattern: LOB pattern to delete.

        Returns:
            True if deleted, False if not found.
        """
        mapping = await self.find_by_pattern(pattern)
        if mapping:
            await self.session.delete(mapping)
            await self.session.flush()
            return True
        return False
