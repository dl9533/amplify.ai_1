# discovery/app/services/activity_service.py
"""Activity service for managing DWA selections."""
from typing import Any, Optional
from uuid import UUID

from app.repositories.activity_selection_repository import ActivitySelectionRepository
from app.repositories.onet_repository import OnetRepository


class ActivityService:
    """Service for DWA activity selection management."""

    # Default threshold for auto-selecting high-exposure activities
    DEFAULT_EXPOSURE_THRESHOLD = 0.6

    def __init__(
        self,
        selection_repository: ActivitySelectionRepository,
        onet_repository: OnetRepository | None = None,
    ) -> None:
        self.selection_repository = selection_repository
        self.onet_repository = onet_repository

    async def load_activities_for_mapping(
        self,
        session_id: UUID,
        role_mapping_id: UUID,
        onet_code: str,
        auto_select_threshold: float = DEFAULT_EXPOSURE_THRESHOLD,
    ) -> list[dict[str, Any]]:
        """Load DWAs for a role mapping and create selections.

        Args:
            session_id: Discovery session ID.
            role_mapping_id: Role mapping ID.
            onet_code: O*NET occupation code.
            auto_select_threshold: Auto-select DWAs above this exposure.

        Returns:
            List of created selection dicts.
        """
        if not self.onet_repository:
            return []

        # Get DWAs for the occupation
        dwas = await self.onet_repository.get_dwas_for_occupation(onet_code)

        selections_data = []
        for dwa in dwas:
            # Get AI exposure score (from DWA override or GWA parent)
            if hasattr(dwa, 'ai_exposure_override') and dwa.ai_exposure_override is not None:
                exposure = dwa.ai_exposure_override
            elif hasattr(dwa, 'iwa') and hasattr(dwa.iwa, 'gwa'):
                exposure = dwa.iwa.gwa.ai_exposure_score or 0.0
            else:
                exposure = 0.0

            # Auto-select if above threshold
            auto_selected = exposure >= auto_select_threshold

            selections_data.append({
                "session_id": session_id,
                "role_mapping_id": role_mapping_id,
                "dwa_id": dwa.id,
                "selected": auto_selected,
                "user_modified": False,
            })

        created = await self.selection_repository.bulk_create(selections_data)

        return [
            {
                "id": str(s.id),
                "dwa_id": s.dwa_id,
                "selected": s.selected,
                "user_modified": s.user_modified,
            }
            for s in created
        ]

    async def get_selections(
        self,
        role_mapping_id: UUID,
    ) -> list[dict[str, Any]]:
        """Get activity selections for a role mapping."""
        selections = await self.selection_repository.get_for_role_mapping(
            role_mapping_id
        )
        return [
            {
                "id": str(s.id),
                "dwa_id": s.dwa_id,
                "selected": s.selected,
                "user_modified": s.user_modified,
            }
            for s in selections
        ]

    async def get_session_selections(
        self,
        session_id: UUID,
    ) -> list[dict[str, Any]]:
        """Get all selections for a session."""
        selections = await self.selection_repository.get_for_session(session_id)
        return [
            {
                "id": str(s.id),
                "role_mapping_id": str(s.role_mapping_id),
                "dwa_id": s.dwa_id,
                "selected": s.selected,
                "user_modified": s.user_modified,
            }
            for s in selections
        ]

    async def update_selection(
        self,
        selection_id: UUID,
        selected: bool,
    ) -> dict[str, Any] | None:
        """Update a selection's status."""
        selection = await self.selection_repository.update_selection(
            selection_id, selected
        )
        if not selection:
            return None
        return {
            "id": str(selection.id),
            "dwa_id": selection.dwa_id,
            "selected": selection.selected,
            "user_modified": selection.user_modified,
        }

    async def bulk_select(
        self,
        session_id: UUID,
        select_all: bool = True,
    ) -> dict[str, int]:
        """Bulk select/deselect all activities for a session."""
        selections = await self.selection_repository.get_for_session(session_id)
        updated = 0

        for selection in selections:
            if selection.selected != select_all:
                await self.selection_repository.update_selection(
                    selection.id, select_all
                )
                updated += 1

        return {"updated_count": updated}

    async def get_activities_by_session(
        self,
        session_id: UUID,
        include_unselected: bool = True,
    ) -> Optional[list[dict]]:
        """Get activities grouped by GWA for a session.

        Args:
            session_id: The session ID to get activities for.
            include_unselected: Whether to include unselected activities.

        Returns:
            List of selection dicts.
        """
        selections = await self.selection_repository.get_for_session(session_id)
        if not include_unselected:
            selections = [s for s in selections if s.selected]

        return [
            {
                "id": str(s.id),
                "role_mapping_id": str(s.role_mapping_id),
                "dwa_id": s.dwa_id,
                "selected": s.selected,
                "user_modified": s.user_modified,
            }
            for s in selections
        ]

    async def bulk_update_selection(
        self,
        session_id: UUID,
        activity_ids: list[UUID],
        selected: bool,
    ) -> Optional[dict]:
        """Bulk update selection status for multiple activities."""
        updated = 0
        for activity_id in activity_ids:
            result = await self.selection_repository.update_selection(
                activity_id, selected
            )
            if result:
                updated += 1
        return {"updated_count": updated}

    async def get_selection_count(
        self,
        session_id: UUID,
    ) -> Optional[dict]:
        """Get selection count statistics for a session."""
        selections = await self.selection_repository.get_for_session(session_id)
        total = len(selections)
        selected = sum(1 for s in selections if s.selected)

        return {
            "total": total,
            "selected": selected,
            "unselected": total - selected,
        }


def get_activity_service() -> ActivityService:
    """Dependency placeholder - will be replaced with DI."""
    raise NotImplementedError("Use dependency injection")
