"""O*NET data repository with full-text search and bulk operations."""
from typing import Any, Sequence
import uuid

from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import OnetOccupation, OnetGWA, OnetIWA, OnetDWA
from app.models.onet_occupation import OnetAlternateTitle, OnetSyncLog
from app.models.onet_task import OnetTask


class OnetRepository:
    """Repository for O*NET reference data operations.

    Provides methods for searching, retrieving, and bulk importing
    O*NET occupation data, alternate titles, tasks, and work activities.
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

        Args:
            keyword: Search keyword.
            limit: Maximum results to return.

        Returns:
            Sequence of matching OnetOccupation objects.
        """
        stmt = (
            select(OnetOccupation)
            .where(OnetOccupation.title.ilike(f"%{keyword}%"))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def search_with_full_text(
        self,
        query: str,
        limit: int = 20,
    ) -> list[OnetOccupation]:
        """Search occupations using PostgreSQL full-text search.

        Searches occupation titles, descriptions, and alternate titles
        using GIN indexes for efficient matching.

        Args:
            query: Search query string.
            limit: Maximum number of results to return.

        Returns:
            List of matching OnetOccupation objects, ranked by relevance.
        """
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
            query: Search query string.
            limit: Maximum results to return.

        Returns:
            Sequence of matching OnetAlternateTitle objects.
        """
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
    # Bulk Upsert Methods
    # ==========================================================================

    async def bulk_upsert_occupations(
        self,
        occupations: list[dict[str, Any]],
    ) -> int:
        """Bulk upsert occupations using PostgreSQL ON CONFLICT.

        Args:
            occupations: List of occupation dicts with code, title, description.

        Returns:
            Number of rows affected.
        """
        if not occupations:
            return 0

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
        await self.session.commit()
        return len(occupations)

    async def bulk_upsert_alternate_titles(
        self,
        titles: list[dict[str, Any]],
    ) -> int:
        """Bulk insert alternate titles (delete existing first).

        Args:
            titles: List of title dicts with id, onet_code, title.

        Returns:
            Number of rows inserted.
        """
        if not titles:
            return 0

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
        await self.session.commit()
        return len(titles)

    async def bulk_upsert_tasks(
        self,
        tasks: list[dict[str, Any]],
    ) -> int:
        """Bulk insert tasks (delete existing first).

        Args:
            tasks: List of task dicts with occupation_code, description, importance.

        Returns:
            Number of rows inserted.
        """
        if not tasks:
            return 0

        # Delete existing tasks
        await self.session.execute(
            text("DELETE FROM onet_tasks")
        )

        # Bulk insert new tasks
        stmt = insert(OnetTask).values(tasks)
        await self.session.execute(stmt)
        await self.session.commit()
        return len(tasks)

    # ==========================================================================
    # Sync Log Methods
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
        await self.session.commit()
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
