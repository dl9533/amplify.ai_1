# discovery/app/repositories/task_selection_repository.py
"""Task selection repository."""
from typing import Sequence
from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.discovery_task_selection import DiscoveryTaskSelection


class TaskSelectionRepository:
    """Repository for task selection operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def bulk_create(
        self,
        selections: list[dict],
    ) -> Sequence[DiscoveryTaskSelection]:
        """Create multiple task selections."""
        db_selections = [DiscoveryTaskSelection(**s) for s in selections]
        self.session.add_all(db_selections)
        await self.session.commit()
        for s in db_selections:
            await self.session.refresh(s)
        return db_selections

    async def get_for_session(
        self,
        session_id: UUID,
    ) -> Sequence[DiscoveryTaskSelection]:
        """Get all task selections for a session."""
        stmt = (
            select(DiscoveryTaskSelection)
            .where(DiscoveryTaskSelection.session_id == session_id)
            .options(joinedload(DiscoveryTaskSelection.task))
        )
        result = await self.session.execute(stmt)
        return result.scalars().unique().all()

    async def get_for_role_mapping(
        self,
        role_mapping_id: UUID,
    ) -> Sequence[DiscoveryTaskSelection]:
        """Get task selections for a specific role mapping."""
        stmt = (
            select(DiscoveryTaskSelection)
            .where(DiscoveryTaskSelection.role_mapping_id == role_mapping_id)
            .options(joinedload(DiscoveryTaskSelection.task))
        )
        result = await self.session.execute(stmt)
        return result.scalars().unique().all()

    async def get_selected_for_role_mapping(
        self,
        role_mapping_id: UUID,
    ) -> Sequence[DiscoveryTaskSelection]:
        """Get only selected task selections for a role mapping."""
        stmt = (
            select(DiscoveryTaskSelection)
            .where(
                DiscoveryTaskSelection.role_mapping_id == role_mapping_id,
                DiscoveryTaskSelection.selected == True,  # noqa: E712
            )
            .options(joinedload(DiscoveryTaskSelection.task))
        )
        result = await self.session.execute(stmt)
        return result.scalars().unique().all()

    async def update_selection(
        self,
        selection_id: UUID,
        selected: bool,
    ) -> DiscoveryTaskSelection | None:
        """Update a selection's selected status."""
        stmt = select(DiscoveryTaskSelection).where(
            DiscoveryTaskSelection.id == selection_id
        )
        result = await self.session.execute(stmt)
        selection = result.scalar_one_or_none()

        if selection:
            selection.selected = selected
            selection.user_modified = True
            await self.session.commit()
            await self.session.refresh(selection)
        return selection

    async def bulk_update_selections(
        self,
        role_mapping_id: UUID,
        task_ids: list[int],
        selected: bool,
    ) -> int:
        """Update selected status for multiple tasks in a role mapping."""
        stmt = (
            select(DiscoveryTaskSelection)
            .where(
                DiscoveryTaskSelection.role_mapping_id == role_mapping_id,
                DiscoveryTaskSelection.task_id.in_(task_ids),
            )
        )
        result = await self.session.execute(stmt)
        selections = result.scalars().all()

        count = 0
        for s in selections:
            s.selected = selected
            s.user_modified = True
            count += 1

        await self.session.commit()
        return count

    async def delete_for_session(self, session_id: UUID) -> int:
        """Delete all task selections for a session."""
        stmt = delete(DiscoveryTaskSelection).where(
            DiscoveryTaskSelection.session_id == session_id
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount

    async def delete_for_role_mapping(self, role_mapping_id: UUID) -> int:
        """Delete all task selections for a role mapping."""
        stmt = delete(DiscoveryTaskSelection).where(
            DiscoveryTaskSelection.role_mapping_id == role_mapping_id
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount

    async def has_tasks_for_role_mapping(self, role_mapping_id: UUID) -> bool:
        """Check if a role mapping already has task selections."""
        from sqlalchemy import func

        stmt = select(func.count()).where(
            DiscoveryTaskSelection.role_mapping_id == role_mapping_id
        )
        result = await self.session.execute(stmt)
        count = result.scalar_one()
        return count > 0

    async def bulk_update_by_role_mapping_ids(
        self,
        role_mapping_ids: list[UUID],
        selected: bool,
    ) -> int:
        """Update selected status for all tasks across multiple role mappings.

        This is more efficient than calling bulk_update_selections for each
        mapping individually, as it performs a single database update.

        Args:
            role_mapping_ids: List of role mapping IDs to update.
            selected: New selection status.

        Returns:
            Number of task selections updated.
        """
        if not role_mapping_ids:
            return 0

        stmt = (
            select(DiscoveryTaskSelection)
            .where(DiscoveryTaskSelection.role_mapping_id.in_(role_mapping_ids))
        )
        result = await self.session.execute(stmt)
        selections = result.scalars().all()

        count = 0
        for s in selections:
            s.selected = selected
            s.user_modified = True
            count += 1

        await self.session.commit()
        return count
