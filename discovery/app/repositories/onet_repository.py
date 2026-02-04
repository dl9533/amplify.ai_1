"""O*NET data repository with full-text search and bulk operations."""
import logging
from typing import Any, Sequence
import uuid

from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import OnetOccupation, OnetGWA, OnetIWA, OnetDWA
from app.models.onet_occupation import OnetAlternateTitle, OnetSyncLog
from app.models.onet_occupation_industry import OnetOccupationIndustry
from app.models.onet_task import OnetTask

logger = logging.getLogger(__name__)


def _escape_ilike(value: str) -> str:
    """Escape special characters for ILIKE pattern matching.

    Prevents SQL pattern injection by escaping ILIKE wildcards.

    Args:
        value: The search string to escape.

    Returns:
        Escaped string safe for ILIKE patterns.
    """
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class OnetRepository:
    """Repository for O*NET reference data operations.

    Provides methods for searching, retrieving, and bulk importing
    O*NET occupation data, alternate titles, tasks, and work activities.

    Note: This repository does NOT manage transactions. The caller (typically
    a service layer) is responsible for committing or rolling back transactions.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy async session.
        """
        self.session = session

    # ==========================================================================
    # Search Methods
    # ==========================================================================

    async def search_occupations(
        self,
        keyword: str,
        limit: int = 20,
    ) -> Sequence[OnetOccupation]:
        """Search occupations by keyword in title (ILIKE).

        Simple keyword search for backwards compatibility.
        Input is escaped to prevent SQL pattern injection.

        Args:
            keyword: Search keyword.
            limit: Maximum results to return.

        Returns:
            Sequence of matching OnetOccupation objects.
        """
        escaped_keyword = _escape_ilike(keyword)
        stmt = (
            select(OnetOccupation)
            .where(OnetOccupation.title.ilike(f"%{escaped_keyword}%", escape="\\"))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    MAX_QUERY_LENGTH = 500  # Maximum search query length

    async def search_with_full_text(
        self,
        query: str,
        limit: int = 20,
    ) -> list[OnetOccupation]:
        """Search occupations using PostgreSQL full-text search.

        Searches occupation titles and descriptions using GIN indexes.
        If fewer than `limit` results are found, also searches alternate
        titles to backfill remaining slots.

        Results are ranked by PostgreSQL's text search ranking algorithm
        based on term frequency and document position.

        Args:
            query: Search query string (max 500 characters).
            limit: Maximum number of results to return.

        Returns:
            List of matching OnetOccupation objects, ranked by relevance.
            Returns empty list for empty/whitespace-only queries.

        Raises:
            ValueError: If query exceeds MAX_QUERY_LENGTH.
        """
        # Input validation
        if not query or not query.strip():
            return []

        query = query.strip()
        if len(query) > self.MAX_QUERY_LENGTH:
            raise ValueError(
                f"Query exceeds maximum length of {self.MAX_QUERY_LENGTH} characters"
            )

        search_query = func.plainto_tsquery("english", query)

        # Search main occupations by title and description
        stmt = (
            select(OnetOccupation)
            .where(
                func.to_tsvector(
                    "english",
                    OnetOccupation.title + " " + func.coalesce(OnetOccupation.description, "")
                ).op("@@")(search_query)
            )
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        occupations = list(result.scalars().all())

        # If not enough results, also search alternate titles
        if len(occupations) < limit:
            remaining = limit - len(occupations)
            existing_codes = {occ.code for occ in occupations}

            alt_stmt = (
                select(OnetOccupation)
                .join(OnetAlternateTitle)
                .where(
                    func.to_tsvector("english", OnetAlternateTitle.title).op("@@")(search_query)
                )
            )
            if existing_codes:
                alt_stmt = alt_stmt.where(OnetOccupation.code.notin_(existing_codes))
            alt_stmt = alt_stmt.limit(remaining)

            alt_result = await self.session.execute(alt_stmt)
            occupations.extend(alt_result.scalars().all())

        return occupations

    async def search_alternate_titles(
        self,
        query: str,
        limit: int = 20,
    ) -> Sequence[OnetAlternateTitle]:
        """Search alternate titles using full-text search.

        Args:
            query: Search query string (max 500 characters).
            limit: Maximum results to return.

        Returns:
            Sequence of matching OnetAlternateTitle objects.
            Returns empty list for empty/whitespace-only queries.

        Raises:
            ValueError: If query exceeds MAX_QUERY_LENGTH.
        """
        # Input validation
        if not query or not query.strip():
            return []

        query = query.strip()
        if len(query) > self.MAX_QUERY_LENGTH:
            raise ValueError(
                f"Query exceeds maximum length of {self.MAX_QUERY_LENGTH} characters"
            )

        search_query = func.plainto_tsquery("english", query)

        stmt = (
            select(OnetAlternateTitle)
            .where(
                func.to_tsvector("english", OnetAlternateTitle.title).op("@@")(search_query)
            )
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return result.scalars().all()

    # ==========================================================================
    # Get Methods
    # ==========================================================================

    async def get_by_code(self, code: str) -> OnetOccupation | None:
        """Get occupation by O*NET code.

        Args:
            code: O*NET occupation code (e.g., "15-1252.00").

        Returns:
            OnetOccupation if found, None otherwise.
        """
        stmt = select(OnetOccupation).where(OnetOccupation.code == code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self) -> Sequence[OnetOccupation]:
        """Get all occupations.

        Note: Returns all ~923 occupations. For large datasets,
        consider pagination.

        Returns:
            Sequence of all OnetOccupation objects.
        """
        stmt = select(OnetOccupation).order_by(OnetOccupation.code)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_alternate_titles_for_occupation(
        self,
        occupation_code: str,
    ) -> Sequence[OnetAlternateTitle]:
        """Get all alternate titles for an occupation.

        Args:
            occupation_code: O*NET occupation code.

        Returns:
            Sequence of OnetAlternateTitle objects.
        """
        stmt = (
            select(OnetAlternateTitle)
            .where(OnetAlternateTitle.onet_code == occupation_code)
            .order_by(OnetAlternateTitle.title)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_gwas(self) -> Sequence[OnetGWA]:
        """Get all Generalized Work Activities.

        Returns:
            Sequence of OnetGWA objects.
        """
        stmt = select(OnetGWA).order_by(OnetGWA.name)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_dwas_for_occupation(
        self,
        occupation_code: str,
    ) -> Sequence[OnetDWA]:
        """Get DWAs associated with an occupation through tasks.

        Args:
            occupation_code: O*NET occupation code.

        Returns:
            Sequence of OnetDWA objects.
        """
        # This will be implemented with proper joins once task-to-dwa mapping exists
        stmt = select(OnetDWA).order_by(OnetDWA.name)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count(self) -> int:
        """Count total occupations in database.

        Returns:
            Total number of occupations.
        """
        stmt = select(func.count()).select_from(OnetOccupation)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    # ==========================================================================
    # Bulk Operations (Transaction managed by caller)
    # ==========================================================================

    async def bulk_upsert_occupations(
        self,
        occupations: list[dict[str, Any]],
    ) -> int:
        """Bulk upsert occupations using PostgreSQL ON CONFLICT.

        Note: Does NOT commit. Caller must manage transaction.

        Args:
            occupations: List of occupation dicts with code, title, description.

        Returns:
            Number of rows affected.
        """
        if not occupations:
            return 0

        logger.info(f"Bulk upserting {len(occupations)} occupations")

        stmt = insert(OnetOccupation).values(occupations)
        stmt = stmt.on_conflict_do_update(
            index_elements=["code"],
            set_={
                "title": stmt.excluded.title,
                "description": stmt.excluded.description,
                "updated_at": func.now(),
            },
        )

        await self.session.execute(stmt)
        return len(occupations)

    async def bulk_replace_alternate_titles(
        self,
        titles: list[dict[str, Any]],
    ) -> int:
        """Replace all alternate titles with new data.

        Deletes all existing alternate titles and inserts new ones.
        Note: Does NOT commit. Caller must manage transaction.

        Args:
            titles: List of title dicts with id, onet_code, title.

        Returns:
            Number of rows inserted.
        """
        if not titles:
            return 0

        logger.info(f"Replacing alternate titles with {len(titles)} records")

        # Delete existing alternate titles
        await self.session.execute(
            text("DELETE FROM onet_alternate_titles")
        )

        # Add UUIDs if not present
        for title in titles:
            if "id" not in title:
                title["id"] = uuid.uuid4()

        # Bulk insert new titles
        stmt = insert(OnetAlternateTitle).values(titles)
        await self.session.execute(stmt)
        return len(titles)

    async def bulk_replace_tasks(
        self,
        tasks: list[dict[str, Any]],
    ) -> int:
        """Replace all tasks with new data.

        Deletes all existing tasks and inserts new ones.
        Note: Does NOT commit. Caller must manage transaction.

        Args:
            tasks: List of task dicts with occupation_code, description, importance.

        Returns:
            Number of rows inserted.
        """
        if not tasks:
            return 0

        logger.info(f"Replacing tasks with {len(tasks)} records")

        # Delete existing tasks
        await self.session.execute(
            text("DELETE FROM onet_tasks")
        )

        # Bulk insert new tasks
        stmt = insert(OnetTask).values(tasks)
        await self.session.execute(stmt)
        return len(tasks)

    # Backwards compatibility aliases
    async def bulk_upsert_alternate_titles(
        self,
        titles: list[dict[str, Any]],
    ) -> int:
        """Alias for bulk_replace_alternate_titles for backwards compatibility."""
        return await self.bulk_replace_alternate_titles(titles)

    async def bulk_upsert_tasks(
        self,
        tasks: list[dict[str, Any]],
    ) -> int:
        """Alias for bulk_replace_tasks for backwards compatibility."""
        return await self.bulk_replace_tasks(tasks)

    # ==========================================================================
    # Sync Log Methods (Transaction managed by caller)
    # ==========================================================================

    async def log_sync(
        self,
        version: str,
        occupation_count: int,
        alternate_title_count: int,
        task_count: int,
        status: str,
    ) -> OnetSyncLog:
        """Log a sync operation.

        Note: Does NOT commit. Caller must manage transaction.

        Args:
            version: O*NET version synced.
            occupation_count: Number of occupations synced.
            alternate_title_count: Number of alternate titles synced.
            task_count: Number of tasks synced.
            status: Sync status (success, failed).

        Returns:
            Created OnetSyncLog record.
        """
        log = OnetSyncLog(
            version=version,
            occupation_count=occupation_count,
            alternate_title_count=alternate_title_count,
            task_count=task_count,
            status=status,
        )
        self.session.add(log)
        await self.session.flush()
        await self.session.refresh(log)
        return log

    async def get_latest_sync(self) -> OnetSyncLog | None:
        """Get the most recent successful sync log.

        Returns:
            Most recent OnetSyncLog with status='success', or None.
        """
        stmt = (
            select(OnetSyncLog)
            .where(OnetSyncLog.status == "success")
            .order_by(OnetSyncLog.synced_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # ==========================================================================
    # Industry Methods
    # ==========================================================================

    async def get_industries_for_occupation(
        self,
        occupation_code: str,
    ) -> list[OnetOccupationIndustry]:
        """Get all industries for an occupation.

        Args:
            occupation_code: O*NET occupation code.

        Returns:
            List of OnetOccupationIndustry objects, ordered by employment percent.
        """
        stmt = select(OnetOccupationIndustry).where(
            OnetOccupationIndustry.occupation_code == occupation_code
        ).order_by(OnetOccupationIndustry.employment_percent.desc().nulls_last())

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def calculate_industry_score(
        self,
        occupation_code: str,
        naics_codes: list[str],
    ) -> float:
        """Calculate industry match score for occupation and NAICS codes.

        Returns 0-1 score based on how well the occupation matches
        the provided industry codes.

        Args:
            occupation_code: O*NET occupation code.
            naics_codes: List of NAICS codes to match against.

        Returns:
            Score from 0.0 (no match) to 1.0 (exact match).
        """
        if not naics_codes:
            return 0.0

        industries = await self.get_industries_for_occupation(occupation_code)
        if not industries:
            return 0.0

        best_score = 0.0
        for industry in industries:
            for target_code in naics_codes:
                score = self._naics_match_score(industry.naics_code, target_code)
                if score > best_score:
                    best_score = score

        return best_score

    def _naics_match_score(self, code1: str, code2: str) -> float:
        """Calculate similarity between two NAICS codes.

        Args:
            code1: First NAICS code.
            code2: Second NAICS code.

        Returns:
            Score from 0.0 to 1.0 based on matching prefix length.
        """
        # Exact match
        if code1 == code2:
            return 1.0

        # Check prefix matching (longer prefix = better match)
        min_len = min(len(code1), len(code2))
        for i in range(min_len, 0, -1):
            if code1[:i] == code2[:i]:
                # Score based on matching prefix length
                if i >= 4:
                    return 0.8
                elif i >= 3:
                    return 0.6
                elif i >= 2:
                    return 0.4

        return 0.0

    async def bulk_upsert_industries(
        self,
        industries: list[dict[str, Any]],
    ) -> int:
        """Bulk upsert occupation-industry mappings.

        Uses PostgreSQL ON CONFLICT for upsert behavior on the
        unique constraint (occupation_code, naics_code).

        Note: Does NOT commit. Caller must manage transaction.

        Args:
            industries: List of industry dicts with occupation_code,
                naics_code, naics_title, employment_percent.

        Returns:
            Number of records upserted.
        """
        if not industries:
            return 0

        logger.info(f"Bulk upserting {len(industries)} industry records")

        stmt = insert(OnetOccupationIndustry).values(industries)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_occ_naics",
            set_={
                "naics_title": stmt.excluded.naics_title,
                "employment_percent": stmt.excluded.employment_percent,
            },
        )

        await self.session.execute(stmt)
        return len(industries)
