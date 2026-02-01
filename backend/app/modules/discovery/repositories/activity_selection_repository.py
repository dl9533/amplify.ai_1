"""Discovery activity selection repository for database operations.

Provides the DiscoveryActivitySelectionRepository for managing DWA (Detailed
Work Activity) selection records including CRUD operations and bulk operations.
"""

from uuid import UUID

from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.discovery.models.session import DiscoveryActivitySelection


class DiscoveryActivitySelectionRepository:
    """Repository for DiscoveryActivitySelection CRUD and query operations.

    Provides async database operations for activity selections including:
    - Create single or bulk activity selections
    - Retrieve selections by ID, session, or role mapping
    - Toggle or update selection state
    - Track user modifications
    - Delete selections individually or by role mapping
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
        role_mapping_id: UUID,
        dwa_id: str,
        selected: bool = True,
        user_modified: bool = False,
    ) -> DiscoveryActivitySelection:
        """Create a new activity selection.

        Creates a selection record for a DWA associated with a role mapping.

        Args:
            session_id: UUID of the discovery session this selection belongs to.
            role_mapping_id: UUID of the role mapping this selection is for.
            dwa_id: ID of the Detailed Work Activity (e.g., "4.A.1.a.1").
            selected: Whether this activity is selected (default True).
            user_modified: Whether the user has modified this selection (default False).

        Returns:
            The created DiscoveryActivitySelection instance.
        """
        selection = DiscoveryActivitySelection(
            session_id=session_id,
            role_mapping_id=role_mapping_id,
            dwa_id=dwa_id,
            selected=selected,
            user_modified=user_modified,
        )
        self.session.add(selection)
        await self.session.commit()
        await self.session.refresh(selection)
        return selection

    async def get_by_id(self, selection_id: UUID) -> DiscoveryActivitySelection | None:
        """Retrieve an activity selection by its ID.

        Args:
            selection_id: UUID of the selection to retrieve.

        Returns:
            DiscoveryActivitySelection if found, None otherwise.
        """
        stmt = select(DiscoveryActivitySelection).where(
            DiscoveryActivitySelection.id == selection_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_session_id(
        self, session_id: UUID
    ) -> list[DiscoveryActivitySelection]:
        """Retrieve all activity selections for a specific session.

        Args:
            session_id: UUID of the session whose selections to retrieve.

        Returns:
            List of DiscoveryActivitySelection instances for the session.
        """
        stmt = select(DiscoveryActivitySelection).where(
            DiscoveryActivitySelection.session_id == session_id
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_role_mapping_id(
        self, role_mapping_id: UUID
    ) -> list[DiscoveryActivitySelection]:
        """Retrieve all activity selections for a specific role mapping.

        Args:
            role_mapping_id: UUID of the role mapping whose selections to retrieve.

        Returns:
            List of DiscoveryActivitySelection instances for the role mapping.
        """
        stmt = select(DiscoveryActivitySelection).where(
            DiscoveryActivitySelection.role_mapping_id == role_mapping_id
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def toggle_selection(
        self, selection_id: UUID
    ) -> DiscoveryActivitySelection | None:
        """Toggle the selected state of an activity selection.

        Flips the selected boolean and sets user_modified=True.

        Args:
            selection_id: UUID of the selection to toggle.

        Returns:
            Updated DiscoveryActivitySelection if found, None otherwise.
        """
        selection = await self.get_by_id(selection_id)
        if selection is None:
            return None

        selection.selected = not selection.selected
        selection.user_modified = True
        await self.session.commit()
        await self.session.refresh(selection)
        return selection

    async def update_selection(
        self, selection_id: UUID, selected: bool
    ) -> DiscoveryActivitySelection | None:
        """Update the selected state of an activity selection.

        Sets the selected value and marks user_modified=True.

        Args:
            selection_id: UUID of the selection to update.
            selected: New selected state value.

        Returns:
            Updated DiscoveryActivitySelection if found, None otherwise.
        """
        selection = await self.get_by_id(selection_id)
        if selection is None:
            return None

        selection.selected = selected
        selection.user_modified = True
        await self.session.commit()
        await self.session.refresh(selection)
        return selection

    async def bulk_create(
        self,
        session_id: UUID,
        role_mapping_id: UUID,
        dwa_ids: list[str],
        selected: bool = True,
    ) -> list[DiscoveryActivitySelection]:
        """Bulk create multiple activity selections.

        Creates selection records for multiple DWAs associated with a role mapping.
        All selections are created with user_modified=False.

        Args:
            session_id: UUID of the discovery session.
            role_mapping_id: UUID of the role mapping.
            dwa_ids: List of Detailed Work Activity IDs to create selections for.
            selected: Whether these activities are selected (default True).

        Returns:
            List of created DiscoveryActivitySelection instances.
        """
        if not dwa_ids:
            return []

        selections = []
        for dwa_id in dwa_ids:
            selection = DiscoveryActivitySelection(
                session_id=session_id,
                role_mapping_id=role_mapping_id,
                dwa_id=dwa_id,
                selected=selected,
                user_modified=False,
            )
            self.session.add(selection)
            selections.append(selection)

        await self.session.commit()

        # Batch refresh: fetch all created selections in a single query
        selection_ids = [s.id for s in selections]
        stmt = select(DiscoveryActivitySelection).where(
            DiscoveryActivitySelection.id.in_(selection_ids)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_selected_for_role_mapping(
        self, role_mapping_id: UUID
    ) -> list[DiscoveryActivitySelection]:
        """Get only selected activities for a role mapping.

        Args:
            role_mapping_id: UUID of the role mapping to get selected activities for.

        Returns:
            List of DiscoveryActivitySelection instances where selected=True.
        """
        stmt = select(DiscoveryActivitySelection).where(
            and_(
                DiscoveryActivitySelection.role_mapping_id == role_mapping_id,
                DiscoveryActivitySelection.selected.is_(True),
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_user_modified(
        self, session_id: UUID
    ) -> list[DiscoveryActivitySelection]:
        """Get all user-modified selections for a session.

        Args:
            session_id: UUID of the session to get modified selections for.

        Returns:
            List of DiscoveryActivitySelection instances where user_modified=True.
        """
        stmt = select(DiscoveryActivitySelection).where(
            and_(
                DiscoveryActivitySelection.session_id == session_id,
                DiscoveryActivitySelection.user_modified.is_(True),
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, selection_id: UUID) -> bool:
        """Delete an activity selection by its ID.

        Args:
            selection_id: UUID of the selection to delete.

        Returns:
            True if the selection was deleted, False if not found.
        """
        selection = await self.get_by_id(selection_id)
        if selection is None:
            return False

        await self.session.delete(selection)
        await self.session.commit()
        return True

    async def delete_by_role_mapping_id(self, role_mapping_id: UUID) -> int:
        """Delete all activity selections for a role mapping.

        Args:
            role_mapping_id: UUID of the role mapping whose selections to delete.

        Returns:
            Number of selections deleted.
        """
        stmt = delete(DiscoveryActivitySelection).where(
            DiscoveryActivitySelection.role_mapping_id == role_mapping_id
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount
