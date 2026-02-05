# discovery/app/services/activity_service.py
"""Activity service for managing DWA selections."""
import logging
from typing import Any, Optional
from uuid import UUID

from app.repositories.activity_selection_repository import ActivitySelectionRepository
from app.repositories.onet_repository import OnetRepository
from app.repositories.role_mapping_repository import RoleMappingRepository

logger = logging.getLogger(__name__)


class ActivityService:
    """Service for DWA activity selection management."""

    # Default threshold for auto-selecting high-exposure activities
    DEFAULT_EXPOSURE_THRESHOLD = 0.6

    def __init__(
        self,
        selection_repository: ActivitySelectionRepository,
        onet_repository: OnetRepository | None = None,
        role_mapping_repository: RoleMappingRepository | None = None,
    ) -> None:
        self.selection_repository = selection_repository
        self.onet_repository = onet_repository
        self.role_mapping_repository = role_mapping_repository

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
            List of GWA group dicts with nested DWA data.
        """
        selections = await self.selection_repository.get_for_session(session_id)
        if not selections:
            return []

        if not include_unselected:
            selections = [s for s in selections if s.selected]

        if not self.onet_repository:
            logger.warning("No O*NET repository available for GWA grouping")
            return []

        # Get all unique DWA IDs from selections
        dwa_ids = list(set(s.dwa_id for s in selections))

        # Get DWA details with GWA hierarchy
        dwas_with_gwa = await self.onet_repository.get_dwas_with_gwa(dwa_ids)

        # Create lookup map for selection data
        selection_map = {s.dwa_id: s for s in selections}

        # Group by GWA
        gwa_groups: dict[str, dict] = {}
        for dwa_data in dwas_with_gwa:
            gwa_code = dwa_data["gwa_id"]
            if gwa_code not in gwa_groups:
                gwa_groups[gwa_code] = {
                    "gwa_code": gwa_code,
                    "gwa_title": dwa_data["gwa_name"],
                    "ai_exposure_score": dwa_data.get("gwa_ai_exposure_score"),
                    "dwas": [],
                }

            selection = selection_map.get(dwa_data["dwa_id"])
            gwa_groups[gwa_code]["dwas"].append({
                "id": str(selection.id) if selection else dwa_data["dwa_id"],
                "code": dwa_data["dwa_id"],
                "title": dwa_data["dwa_name"],
                "description": dwa_data.get("dwa_description"),
                "selected": selection.selected if selection else False,
                "gwa_code": gwa_code,
            })

        return list(gwa_groups.values())

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
            "gwas_with_selections": 0,  # TODO: implement GWA grouping
        }

    async def load_activities_for_session(
        self,
        session_id: UUID,
        auto_select_threshold: float = DEFAULT_EXPOSURE_THRESHOLD,
    ) -> Optional[dict[str, Any]]:
        """Load DWA activities for all confirmed role mappings in a session.

        This should be called after role mappings are confirmed to populate
        the activities selection table with DWAs for each O*NET occupation.

        Args:
            session_id: Discovery session ID.
            auto_select_threshold: Auto-select DWAs above this exposure.

        Returns:
            Dictionary with load statistics, or None if session not found.
        """
        if not self.role_mapping_repository or not self.onet_repository:
            logger.warning("Missing repositories for loading activities")
            return {"mappings_processed": 0, "activities_loaded": 0}

        # Get all role mappings for the session
        mappings = await self.role_mapping_repository.get_for_session(session_id)
        if not mappings:
            logger.info(f"No role mappings found for session {session_id}")
            return None

        # Extract data synchronously to avoid async context issues
        # Filter for confirmed mappings with O*NET codes
        confirmed_mapping_data = [
            {
                "id": m.id,
                "source_role": m.source_role,
                "onet_code": m.onet_code,
            }
            for m in mappings
            if m.user_confirmed and m.onet_code
        ]

        logger.info(
            f"Loading activities for {len(confirmed_mapping_data)} confirmed mappings "
            f"(out of {len(mappings)} total) in session {session_id}"
        )

        total_activities = 0
        mappings_processed = 0

        for mapping_data in confirmed_mapping_data:
            try:
                created = await self.load_activities_for_mapping(
                    session_id=session_id,
                    role_mapping_id=mapping_data["id"],
                    onet_code=mapping_data["onet_code"],
                    auto_select_threshold=auto_select_threshold,
                )
                activities_count = len(created)
                total_activities += activities_count
                mappings_processed += 1
                logger.debug(
                    f"Loaded {activities_count} activities for mapping "
                    f"{mapping_data['source_role']} -> {mapping_data['onet_code']}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to load activities for mapping {mapping_data['id']}: {e}"
                )

        logger.info(
            f"Loaded {total_activities} activities for {mappings_processed} mappings"
        )

        return {
            "mappings_processed": mappings_processed,
            "activities_loaded": total_activities,
        }


from collections.abc import AsyncGenerator


async def get_activity_service() -> AsyncGenerator[ActivityService, None]:
    """Get activity service dependency for FastAPI.

    Yields a fully configured ActivityService with selection, O*NET, and role mapping repositories.
    """
    from app.models.base import async_session_maker
    from app.repositories.onet_repository import OnetRepository

    async with async_session_maker() as db:
        selection_repository = ActivitySelectionRepository(db)
        onet_repository = OnetRepository(db)
        role_mapping_repository = RoleMappingRepository(db)
        service = ActivityService(
            selection_repository=selection_repository,
            onet_repository=onet_repository,
            role_mapping_repository=role_mapping_repository,
        )
        yield service
