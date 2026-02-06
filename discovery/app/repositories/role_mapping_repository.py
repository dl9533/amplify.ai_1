"""Discovery role mapping repository."""
from typing import Sequence
from uuid import UUID

from sqlalchemy import delete, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.discovery_role_mapping import DiscoveryRoleMapping


class RoleMappingRepository:
    """Repository for role mapping operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        session_id: UUID,
        source_role: str,
        onet_code: str | None = None,
        confidence_score: float | None = None,
        row_count: int | None = None,
        industry_match_score: float | None = None,
        lob_value: str | None = None,
    ) -> DiscoveryRoleMapping:
        """Create a single role mapping.

        Args:
            session_id: Discovery session ID.
            source_role: Original role title from the upload.
            onet_code: Mapped O*NET occupation code.
            confidence_score: Confidence score of the mapping.
            row_count: Number of employees with this role.
            industry_match_score: Industry match score for boosting.
            lob_value: Line of Business value for grouping.

        Returns:
            Created role mapping record.
        """
        mapping = DiscoveryRoleMapping(
            session_id=session_id,
            source_role=source_role,
            onet_code=onet_code,
            confidence_score=confidence_score,
            row_count=row_count,
            industry_match_score=industry_match_score,
            lob_value=lob_value,
        )
        self.session.add(mapping)
        await self.session.commit()
        await self.session.refresh(mapping)
        return mapping

    async def bulk_create(
        self,
        mappings: list[dict],
    ) -> Sequence[DiscoveryRoleMapping]:
        """Create multiple role mappings at once."""
        db_mappings = [DiscoveryRoleMapping(**m) for m in mappings]
        self.session.add_all(db_mappings)
        await self.session.commit()
        for m in db_mappings:
            await self.session.refresh(m)
        return db_mappings

    async def bulk_upsert(
        self,
        mappings: list[dict],
    ) -> Sequence[DiscoveryRoleMapping]:
        """Create or update multiple role mappings using upsert.

        Uses PostgreSQL ON CONFLICT to handle duplicates based on
        (session_id, source_role, lob_value) unique constraint.
        On conflict, updates the O*NET code, confidence score, and row count.

        Args:
            mappings: List of mapping dicts with session_id, source_role, etc.

        Returns:
            List of created/updated role mappings.
        """
        if not mappings:
            return []

        # Use raw SQL for the upsert since SQLAlchemy's insert().on_conflict_do_update()
        # doesn't work well with functional indexes (COALESCE)
        for m in mappings:
            # Check if mapping exists
            stmt = select(DiscoveryRoleMapping).where(
                DiscoveryRoleMapping.session_id == m["session_id"],
                DiscoveryRoleMapping.source_role == m["source_role"],
                # Handle NULL lob_value comparison
                (DiscoveryRoleMapping.lob_value == m.get("lob_value"))
                if m.get("lob_value")
                else DiscoveryRoleMapping.lob_value.is_(None),
            )
            result = await self.session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing mapping
                if m.get("onet_code") is not None:
                    existing.onet_code = m["onet_code"]
                if m.get("confidence_score") is not None:
                    existing.confidence_score = m["confidence_score"]
                if m.get("row_count") is not None:
                    existing.row_count = (existing.row_count or 0) + m["row_count"]
                if m.get("industry_match_score") is not None:
                    existing.industry_match_score = m["industry_match_score"]
            else:
                # Create new mapping
                db_mapping = DiscoveryRoleMapping(**m)
                self.session.add(db_mapping)

        await self.session.commit()

        # Return all mappings for the session
        if mappings:
            session_id = mappings[0]["session_id"]
            return await self.get_for_session(session_id)
        return []

    async def get_for_session(
        self,
        session_id: UUID,
    ) -> Sequence[DiscoveryRoleMapping]:
        """Get all mappings for a session."""
        stmt = (
            select(DiscoveryRoleMapping)
            .where(DiscoveryRoleMapping.session_id == session_id)
            .order_by(DiscoveryRoleMapping.source_role)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def confirm(
        self,
        mapping_id: UUID,
        onet_code: str,
    ) -> DiscoveryRoleMapping | None:
        """Confirm a role mapping with selected O*NET code."""
        stmt = select(DiscoveryRoleMapping).where(DiscoveryRoleMapping.id == mapping_id)
        result = await self.session.execute(stmt)
        mapping = result.scalar_one_or_none()

        if mapping:
            mapping.onet_code = onet_code
            mapping.user_confirmed = True
            await self.session.commit()
            await self.session.refresh(mapping)
        return mapping

    async def update(
        self,
        mapping_id: UUID,
        onet_code: str | None = None,
        user_confirmed: bool | None = None,
        confidence_score: float | None = None,
    ) -> DiscoveryRoleMapping | None:
        """Update a role mapping.

        Args:
            mapping_id: The mapping ID to update.
            onet_code: New O*NET code (optional).
            user_confirmed: New confirmation status (optional).
            confidence_score: New confidence score (optional).

        Returns:
            Updated mapping or None if not found.
        """
        stmt = select(DiscoveryRoleMapping).where(DiscoveryRoleMapping.id == mapping_id)
        result = await self.session.execute(stmt)
        mapping = result.scalar_one_or_none()

        if mapping:
            if onet_code is not None:
                mapping.onet_code = onet_code
            if user_confirmed is not None:
                mapping.user_confirmed = user_confirmed
            if confidence_score is not None:
                mapping.confidence_score = confidence_score
            await self.session.commit()
            await self.session.refresh(mapping)
        return mapping

    async def delete_for_session(
        self,
        session_id: UUID,
    ) -> int:
        """Delete all mappings for a session.

        Args:
            session_id: Session ID to delete mappings for.

        Returns:
            Number of mappings deleted.
        """
        stmt = delete(DiscoveryRoleMapping).where(
            DiscoveryRoleMapping.session_id == session_id
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount or 0
