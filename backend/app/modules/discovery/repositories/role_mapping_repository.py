"""Discovery role mapping repository for database operations.

Provides the DiscoveryRoleMappingRepository for managing role mapping
records including CRUD operations and O*NET code mapping queries.
"""

from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.discovery.models.session import DiscoveryRoleMapping


class DiscoveryRoleMappingRepository:
    """Repository for DiscoveryRoleMapping CRUD and query operations.

    Provides async database operations for role mappings including:
    - Create new role mappings with O*NET codes
    - Retrieve mappings by ID, session, or source role
    - Update O*NET codes and confidence scores
    - Confirm mappings individually or in bulk
    - Delete mappings
    - Get unconfirmed mappings for review
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy async session for database operations.
        """
        self.session = session

    async def create(
        self,
        session_id: UUID,
        source_role: str,
        onet_code: str | None,
        confidence_score: float | None = None,
        user_confirmed: bool = False,
        row_count: int | None = None,
    ) -> DiscoveryRoleMapping:
        """Create a new role mapping.

        Creates a mapping between a customer role and an O*NET occupation code.

        Args:
            session_id: UUID of the discovery session this mapping belongs to.
            source_role: The customer's role name from their data.
            onet_code: O*NET occupation code (e.g., "15-1252.00"), or None.
            confidence_score: AI confidence score for the mapping (0.0-1.0).
            user_confirmed: Whether a user has confirmed this mapping.
            row_count: Number of rows in source data with this role.

        Returns:
            The created DiscoveryRoleMapping instance.
        """
        mapping = DiscoveryRoleMapping(
            session_id=session_id,
            source_role=source_role,
            onet_code=onet_code,
            confidence_score=confidence_score,
            user_confirmed=user_confirmed,
            row_count=row_count,
        )
        self.session.add(mapping)
        await self.session.commit()
        await self.session.refresh(mapping)
        return mapping

    async def get_by_id(self, mapping_id: UUID) -> DiscoveryRoleMapping | None:
        """Retrieve a role mapping by its ID.

        Args:
            mapping_id: UUID of the mapping to retrieve.

        Returns:
            DiscoveryRoleMapping if found, None otherwise.
        """
        stmt = select(DiscoveryRoleMapping).where(DiscoveryRoleMapping.id == mapping_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_session_id(self, session_id: UUID) -> list[DiscoveryRoleMapping]:
        """Retrieve all role mappings for a specific session.

        Args:
            session_id: UUID of the session whose mappings to retrieve.

        Returns:
            List of DiscoveryRoleMapping instances for the session.
        """
        stmt = select(DiscoveryRoleMapping).where(
            DiscoveryRoleMapping.session_id == session_id
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_onet_code(
        self,
        mapping_id: UUID,
        onet_code: str,
        user_confirmed: bool = True,
    ) -> DiscoveryRoleMapping | None:
        """Update the O*NET code for a mapping.

        Args:
            mapping_id: UUID of the mapping to update.
            onet_code: New O*NET occupation code.
            user_confirmed: Whether to mark as user confirmed (default True).

        Returns:
            Updated DiscoveryRoleMapping if found, None otherwise.
        """
        mapping = await self.get_by_id(mapping_id)
        if mapping is None:
            return None

        mapping.onet_code = onet_code
        mapping.user_confirmed = user_confirmed
        await self.session.commit()
        await self.session.refresh(mapping)
        return mapping

    async def update_confidence_score(
        self,
        mapping_id: UUID,
        confidence_score: float,
    ) -> DiscoveryRoleMapping | None:
        """Update the confidence score for a mapping.

        Args:
            mapping_id: UUID of the mapping to update.
            confidence_score: New confidence score (0.0-1.0).

        Returns:
            Updated DiscoveryRoleMapping if found, None otherwise.
        """
        mapping = await self.get_by_id(mapping_id)
        if mapping is None:
            return None

        mapping.confidence_score = confidence_score
        await self.session.commit()
        await self.session.refresh(mapping)
        return mapping

    async def confirm_mapping(self, mapping_id: UUID) -> DiscoveryRoleMapping | None:
        """Confirm a mapping by setting user_confirmed to True.

        Args:
            mapping_id: UUID of the mapping to confirm.

        Returns:
            Updated DiscoveryRoleMapping if found, None otherwise.
        """
        mapping = await self.get_by_id(mapping_id)
        if mapping is None:
            return None

        mapping.user_confirmed = True
        await self.session.commit()
        await self.session.refresh(mapping)
        return mapping

    async def bulk_confirm_above_threshold(
        self,
        session_id: UUID,
        threshold: float,
    ) -> int:
        """Confirm all mappings above a confidence threshold.

        Finds all unconfirmed mappings for the session with confidence
        scores >= threshold and marks them as user_confirmed.

        Args:
            session_id: UUID of the session whose mappings to confirm.
            threshold: Minimum confidence score to auto-confirm.

        Returns:
            Number of mappings confirmed.
        """
        stmt = select(DiscoveryRoleMapping).where(
            and_(
                DiscoveryRoleMapping.session_id == session_id,
                DiscoveryRoleMapping.user_confirmed == False,  # noqa: E712
                DiscoveryRoleMapping.confidence_score >= threshold,
            )
        )
        result = await self.session.execute(stmt)
        mappings = list(result.scalars().all())

        for mapping in mappings:
            mapping.user_confirmed = True

        if mappings:
            await self.session.commit()

        return len(mappings)

    async def get_unconfirmed(self, session_id: UUID) -> list[DiscoveryRoleMapping]:
        """Get all unconfirmed mappings for a session.

        Args:
            session_id: UUID of the session whose unconfirmed mappings to get.

        Returns:
            List of unconfirmed DiscoveryRoleMapping instances.
        """
        stmt = select(DiscoveryRoleMapping).where(
            and_(
                DiscoveryRoleMapping.session_id == session_id,
                DiscoveryRoleMapping.user_confirmed == False,  # noqa: E712
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, mapping_id: UUID) -> bool:
        """Delete a role mapping by its ID.

        Args:
            mapping_id: UUID of the mapping to delete.

        Returns:
            True if the mapping was deleted, False if not found.
        """
        mapping = await self.get_by_id(mapping_id)
        if mapping is None:
            return False

        await self.session.delete(mapping)
        await self.session.commit()
        return True

    async def get_by_source_role(
        self,
        session_id: UUID,
        source_role: str,
    ) -> DiscoveryRoleMapping | None:
        """Retrieve a mapping by source role name within a session.

        Args:
            session_id: UUID of the session to search in.
            source_role: The source role name to find.

        Returns:
            DiscoveryRoleMapping if found, None otherwise.
        """
        stmt = select(DiscoveryRoleMapping).where(
            and_(
                DiscoveryRoleMapping.session_id == session_id,
                DiscoveryRoleMapping.source_role == source_role,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
