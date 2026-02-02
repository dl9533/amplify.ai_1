# discovery/app/repositories/activity_selection_repository.py
"""Activity selection repository."""
from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.discovery_activity_selection import DiscoveryActivitySelection


class ActivitySelectionRepository:
    """Repository for activity selection operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def bulk_create(
        self,
        selections: list[dict],
    ) -> Sequence[DiscoveryActivitySelection]:
        """Create multiple activity selections."""
        db_selections = [DiscoveryActivitySelection(**s) for s in selections]
        self.session.add_all(db_selections)
        await self.session.commit()
        for s in db_selections:
            await self.session.refresh(s)
        return db_selections

    async def get_for_session(
        self,
        session_id: UUID,
    ) -> Sequence[DiscoveryActivitySelection]:
        """Get all selections for a session."""
        stmt = (
            select(DiscoveryActivitySelection)
            .where(DiscoveryActivitySelection.session_id == session_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_for_role_mapping(
        self,
        role_mapping_id: UUID,
    ) -> Sequence[DiscoveryActivitySelection]:
        """Get selections for a specific role mapping."""
        stmt = (
            select(DiscoveryActivitySelection)
            .where(DiscoveryActivitySelection.role_mapping_id == role_mapping_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_selection(
        self,
        selection_id: UUID,
        selected: bool,
    ) -> DiscoveryActivitySelection | None:
        """Update a selection's selected status."""
        stmt = select(DiscoveryActivitySelection).where(
            DiscoveryActivitySelection.id == selection_id
        )
        result = await self.session.execute(stmt)
        selection = result.scalar_one_or_none()

        if selection:
            selection.selected = selected
            selection.user_modified = True
            await self.session.commit()
            await self.session.refresh(selection)
        return selection

    async def delete_for_session(self, session_id: UUID) -> int:
        """Delete all selections for a session."""
        stmt = select(DiscoveryActivitySelection).where(
            DiscoveryActivitySelection.session_id == session_id
        )
        result = await self.session.execute(stmt)
        selections = result.scalars().all()

        count = len(selections)
        for s in selections:
            await self.session.delete(s)
        await self.session.commit()
        return count
