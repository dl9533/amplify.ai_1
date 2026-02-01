"""Discovery role mapping repository."""
from typing import Sequence
from uuid import UUID

from sqlalchemy import select
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
    ) -> DiscoveryRoleMapping:
        """Create a single role mapping."""
        mapping = DiscoveryRoleMapping(
            session_id=session_id,
            source_role=source_role,
            onet_code=onet_code,
            confidence_score=confidence_score,
            row_count=row_count,
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
