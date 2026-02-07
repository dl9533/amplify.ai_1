"""Discovery role mapping repository."""
import logging
from typing import Sequence
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import lazyload

from app.models.discovery_role_mapping import DiscoveryRoleMapping

logger = logging.getLogger(__name__)

# Maximum PostgreSQL INTEGER value for bounds checking
MAX_ROW_COUNT = 2_147_483_647

# The unique constraint name for duplicate detection
UNIQUE_CONSTRAINT_NAME = "uq_role_mapping_session_role_lob"


def _normalize_lob_value(lob_value: str | None) -> str | None:
    """Normalize LOB value to match database COALESCE behavior.

    The unique constraint uses COALESCE(lob_value, '') which treats
    NULL and empty string as equivalent. This function normalizes
    both to None for consistent comparison in Python.

    Args:
        lob_value: The LOB value to normalize.

    Returns:
        None if the value is None or empty string, otherwise the original value.
    """
    if lob_value is None or lob_value == "":
        return None
    return lob_value


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
        department_value: str | None = None,
        geography_value: str | None = None,
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
            department_value: Department value for grouping.
            geography_value: Geography/location value for grouping.

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
            department_value=department_value,
            geography_value=geography_value,
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
        replace_counts: bool = True,
    ) -> Sequence[DiscoveryRoleMapping]:
        """Create or update multiple role mappings using upsert.

        Uses row-level locking (SELECT FOR UPDATE) to handle duplicates based on
        (session_id, source_role, lob_value) unique constraint.
        On conflict, updates all mapping fields.

        Args:
            mappings: List of mapping dicts with session_id, source_role, etc.
            replace_counts: If True, replace row_count values. If False, add to existing.

        Returns:
            List of created/updated role mappings.

        Raises:
            ValueError: If required fields are missing from mapping dicts.
        """
        if not mappings:
            return []

        # Validate required fields upfront
        for i, m in enumerate(mappings):
            if "session_id" not in m:
                raise ValueError(f"Mapping at index {i} missing required field: session_id")
            if "source_role" not in m:
                raise ValueError(f"Mapping at index {i} missing required field: source_role")

        # Use SELECT FOR UPDATE to prevent race conditions when multiple
        # requests try to upsert the same role mapping concurrently.
        # SQLAlchemy's insert().on_conflict_do_update() doesn't work well
        # with functional indexes (COALESCE), so we use explicit locking.
        created_mappings: list[DiscoveryRoleMapping] = []

        for m in mappings:
            # Normalize lob_value to match database COALESCE behavior
            # The unique constraint treats NULL and '' as equivalent
            lob_value = _normalize_lob_value(m.get("lob_value"))

            # Check if mapping exists with row-level lock to prevent races
            # Use consistent NULL/empty string handling for lookup
            if lob_value is None:
                # Match both NULL and empty string in the database
                # since COALESCE(lob_value, '') treats them as equivalent
                lob_condition = (
                    (DiscoveryRoleMapping.lob_value.is_(None)) |
                    (DiscoveryRoleMapping.lob_value == "")
                )
            else:
                lob_condition = DiscoveryRoleMapping.lob_value == lob_value

            stmt = (
                select(DiscoveryRoleMapping)
                .where(
                    DiscoveryRoleMapping.session_id == m["session_id"],
                    DiscoveryRoleMapping.source_role == m["source_role"],
                    lob_condition,
                )
                # Use lazyload to prevent eager loading of relationships
                # This avoids "FOR UPDATE cannot be applied to outer join" error
                .options(lazyload("*"))
                .with_for_update()
            )
            result = await self.session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing mapping with all provided fields
                if m.get("onet_code") is not None:
                    existing.onet_code = m["onet_code"]
                if m.get("confidence_score") is not None:
                    existing.confidence_score = m["confidence_score"]
                if m.get("row_count") is not None:
                    if replace_counts:
                        # Replace with new value (used after delete)
                        existing.row_count = min(m["row_count"], MAX_ROW_COUNT)
                    else:
                        # Add to existing (incremental update)
                        new_count = (existing.row_count or 0) + m["row_count"]
                        existing.row_count = min(new_count, MAX_ROW_COUNT)
                if m.get("industry_match_score") is not None:
                    existing.industry_match_score = m["industry_match_score"]
                if m.get("department_value") is not None:
                    existing.department_value = m["department_value"]
                if m.get("geography_value") is not None:
                    existing.geography_value = m["geography_value"]
                created_mappings.append(existing)
            else:
                # Create new mapping with normalized lob_value
                mapping_data = m.copy()
                mapping_data["lob_value"] = lob_value
                try:
                    db_mapping = DiscoveryRoleMapping(**mapping_data)
                    self.session.add(db_mapping)
                    # Flush to detect constraint violations early
                    await self.session.flush()
                    created_mappings.append(db_mapping)
                except IntegrityError as e:
                    # Handle race condition: another transaction inserted first
                    if UNIQUE_CONSTRAINT_NAME in str(e.orig):
                        logger.warning(
                            f"Race condition detected for role mapping: "
                            f"session={m['session_id']}, role={m['source_role']}, lob={lob_value}. "
                            "Fetching existing record."
                        )
                        await self.session.rollback()
                        # Re-fetch the existing record that was just inserted
                        result = await self.session.execute(stmt)
                        existing = result.scalar_one_or_none()
                        if existing:
                            created_mappings.append(existing)
                        else:
                            # This shouldn't happen, but log and continue
                            logger.error(
                                f"Failed to find existing mapping after race condition: "
                                f"session={m['session_id']}, role={m['source_role']}, lob={lob_value}"
                            )
                    else:
                        # Different integrity error - re-raise
                        raise

        await self.session.commit()

        # Refresh all created/updated mappings to get database-generated fields
        for mapping in created_mappings:
            await self.session.refresh(mapping)

        return created_mappings

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

    async def get_by_id(
        self,
        mapping_id: UUID,
        session_id: UUID | None = None,
    ) -> DiscoveryRoleMapping | None:
        """Get a single role mapping by ID.

        Args:
            mapping_id: The role mapping ID.
            session_id: Optional session ID for authorization validation.
                       If provided, only returns the mapping if it belongs
                       to the specified session (prevents cross-session access).

        Returns:
            The role mapping or None if not found (or unauthorized).
        """
        stmt = select(DiscoveryRoleMapping).where(DiscoveryRoleMapping.id == mapping_id)
        if session_id is not None:
            stmt = stmt.where(DiscoveryRoleMapping.session_id == session_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

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
