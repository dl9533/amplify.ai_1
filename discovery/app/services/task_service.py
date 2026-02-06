# discovery/app/services/task_service.py
"""Task service for managing task selections."""
import logging
from collections.abc import AsyncGenerator
from typing import Any
from uuid import UUID

from app.repositories.task_selection_repository import TaskSelectionRepository
from app.repositories.onet_repository import OnetRepository
from app.repositories.role_mapping_repository import RoleMappingRepository

logger = logging.getLogger(__name__)


class TaskService:
    """Service for task selection management.

    Manages the selection of O*NET tasks for confirmed role mappings.
    Selected tasks are used for AI impact analysis via the Task → DWA chain.
    """

    def __init__(
        self,
        selection_repository: TaskSelectionRepository,
        onet_repository: OnetRepository | None = None,
        role_mapping_repository: RoleMappingRepository | None = None,
    ) -> None:
        self.selection_repository = selection_repository
        self.onet_repository = onet_repository
        self.role_mapping_repository = role_mapping_repository

    async def load_tasks_for_mapping(
        self,
        session_id: UUID,
        role_mapping_id: UUID,
        onet_code: str,
    ) -> list[dict[str, Any]]:
        """Load tasks for a role mapping and create selections.

        All tasks are selected by default. Users can deselect tasks
        they don't want included in AI impact analysis.

        This operation is idempotent - if tasks already exist for the
        role mapping, it returns an empty list without creating duplicates.

        Args:
            session_id: Discovery session ID.
            role_mapping_id: Role mapping ID.
            onet_code: O*NET occupation code.

        Returns:
            List of created selection dicts, empty if already loaded.
        """
        if not self.onet_repository:
            return []

        # Check if tasks already exist (idempotency)
        has_tasks = await self.selection_repository.has_tasks_for_role_mapping(
            role_mapping_id
        )
        if has_tasks:
            logger.debug(
                f"Tasks already loaded for mapping {role_mapping_id}, skipping"
            )
            return []

        # Get tasks for the occupation
        tasks = await self.onet_repository.get_tasks_for_occupation(onet_code)

        if not tasks:
            logger.warning(f"No tasks found for occupation {onet_code}")
            return []

        selections_data = []
        for task in tasks:
            selections_data.append({
                "session_id": session_id,
                "role_mapping_id": role_mapping_id,
                "task_id": task.id,
                "selected": True,  # All tasks selected by default
                "user_modified": False,
            })

        created = await self.selection_repository.bulk_create(selections_data)

        return [
            {
                "id": str(s.id),
                "task_id": s.task_id,
                "description": s.task.description if s.task else None,
                "selected": s.selected,
                "user_modified": s.user_modified,
            }
            for s in created
        ]

    async def load_tasks_for_session(
        self,
        session_id: UUID,
    ) -> dict[str, Any] | None:
        """Load tasks for all confirmed role mappings in a session.

        This should be called after role mappings are confirmed to populate
        the task selection table with tasks for each O*NET occupation.

        Args:
            session_id: Discovery session ID.

        Returns:
            Dictionary with load statistics, or None if session not found.
        """
        if not self.role_mapping_repository or not self.onet_repository:
            logger.warning("Missing repositories for loading tasks")
            return {"mappings_processed": 0, "tasks_loaded": 0}

        # Get all role mappings for the session
        mappings = await self.role_mapping_repository.get_for_session(session_id)
        if not mappings:
            logger.info(f"No role mappings found for session {session_id}")
            return None

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
            f"Loading tasks for {len(confirmed_mapping_data)} confirmed mappings "
            f"(out of {len(mappings)} total) in session {session_id}"
        )

        total_tasks = 0
        mappings_processed = 0

        for mapping_data in confirmed_mapping_data:
            try:
                created = await self.load_tasks_for_mapping(
                    session_id=session_id,
                    role_mapping_id=mapping_data["id"],
                    onet_code=mapping_data["onet_code"],
                )
                tasks_count = len(created)
                total_tasks += tasks_count
                mappings_processed += 1
                logger.debug(
                    f"Loaded {tasks_count} tasks for mapping "
                    f"{mapping_data['source_role']} -> {mapping_data['onet_code']}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to load tasks for mapping {mapping_data['id']}: {e}"
                )

        logger.info(
            f"Loaded {total_tasks} tasks for {mappings_processed} mappings"
        )

        return {
            "mappings_processed": mappings_processed,
            "tasks_loaded": total_tasks,
        }

    async def get_tasks_for_role_mapping(
        self,
        role_mapping_id: UUID,
    ) -> list[dict[str, Any]]:
        """Get task selections for a role mapping with task details.

        Args:
            role_mapping_id: Role mapping ID.

        Returns:
            List of task selection dicts with task details.
        """
        selections = await self.selection_repository.get_for_role_mapping(
            role_mapping_id
        )

        return [
            {
                "id": str(s.id),
                "role_mapping_id": str(s.role_mapping_id),
                "task_id": s.task_id,
                "description": s.task.description if s.task else None,
                "importance": s.task.importance if s.task else None,
                "selected": s.selected,
                "user_modified": s.user_modified,
            }
            for s in selections
        ]

    async def get_tasks_for_session(
        self,
        session_id: UUID,
        include_unselected: bool = True,
    ) -> list[dict[str, Any]]:
        """Get all task selections for a session grouped by role mapping.

        Args:
            session_id: Discovery session ID.
            include_unselected: Whether to include unselected tasks.

        Returns:
            List of task selection dicts.
        """
        selections = await self.selection_repository.get_for_session(session_id)

        if not include_unselected:
            selections = [s for s in selections if s.selected]

        return [
            {
                "id": str(s.id),
                "role_mapping_id": str(s.role_mapping_id),
                "task_id": s.task_id,
                "description": s.task.description if s.task else None,
                "importance": s.task.importance if s.task else None,
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
        """Update a task selection's status.

        Args:
            selection_id: Selection ID.
            selected: New selected status.

        Returns:
            Updated selection dict or None if not found.
        """
        selection = await self.selection_repository.update_selection(
            selection_id, selected
        )
        if not selection:
            return None

        return {
            "id": str(selection.id),
            "role_mapping_id": str(selection.role_mapping_id),
            "task_id": selection.task_id,
            "description": selection.task.description if selection.task else None,
            "importance": selection.task.importance if selection.task else None,
            "selected": selection.selected,
            "user_modified": selection.user_modified,
        }

    async def bulk_update_selections(
        self,
        role_mapping_id: UUID,
        task_ids: list[int],
        selected: bool,
    ) -> dict[str, int]:
        """Bulk update selection status for multiple tasks.

        Args:
            role_mapping_id: Role mapping ID.
            task_ids: List of task IDs to update.
            selected: New selected status.

        Returns:
            Dict with updated count.
        """
        updated = await self.selection_repository.bulk_update_selections(
            role_mapping_id, task_ids, selected
        )
        return {"updated_count": updated}

    async def get_tasks_grouped_by_mapping(
        self,
        session_id: UUID,
    ) -> list[dict[str, Any]]:
        """Get tasks grouped by role mapping for efficient frontend loading.

        This method returns all tasks for a session in a single query,
        grouped by their role mapping. Used to avoid N+1 queries in the frontend.

        Args:
            session_id: Discovery session ID.

        Returns:
            List of role mapping dicts with their tasks.
        """
        if not self.role_mapping_repository:
            return []

        # Get confirmed role mappings
        mappings = await self.role_mapping_repository.get_for_session(session_id)
        confirmed = [m for m in mappings if m.user_confirmed and m.onet_code]

        if not confirmed:
            return []

        # Get all tasks for session in one query
        selections = await self.selection_repository.get_for_session(session_id)

        # Group by role_mapping_id
        tasks_by_mapping: dict[str, list[dict[str, Any]]] = {}
        for s in selections:
            mapping_id = str(s.role_mapping_id)
            if mapping_id not in tasks_by_mapping:
                tasks_by_mapping[mapping_id] = []
            tasks_by_mapping[mapping_id].append({
                "id": str(s.id),
                "role_mapping_id": mapping_id,
                "task_id": s.task_id,
                "description": s.task.description if s.task else None,
                "importance": s.task.importance if s.task else None,
                "selected": s.selected,
                "user_modified": s.user_modified,
            })

        # Build response with mapping info
        results = []
        for m in confirmed:
            mapping_id = str(m.id)
            results.append({
                "role_mapping_id": mapping_id,
                "source_role": m.source_role,
                "onet_code": m.onet_code,
                "onet_title": m.onet_title,
                "tasks": tasks_by_mapping.get(mapping_id, []),
            })

        return results

    async def get_tasks_grouped_by_lob(
        self,
        session_id: UUID,
    ) -> dict[str, Any]:
        """Get tasks grouped by LOB and O*NET occupation.

        This groups tasks hierarchically:
        - LOB (Line of Business)
          └── O*NET Occupation (deduplicated by code)
               └── Tasks

        Multiple role mappings with the same O*NET code within a LOB
        are consolidated, showing tasks just once per occupation.

        Args:
            session_id: Discovery session ID.

        Returns:
            Dict with session_id, overall_summary, lob_groups, ungrouped_occupations.
        """
        if not self.role_mapping_repository:
            return {
                "session_id": str(session_id),
                "overall_summary": {
                    "total_tasks": 0,
                    "selected_count": 0,
                    "occupation_count": 0,
                    "total_employees": 0,
                },
                "lob_groups": [],
                "ungrouped_occupations": [],
            }

        # Get confirmed role mappings
        mappings = await self.role_mapping_repository.get_for_session(session_id)
        confirmed = [m for m in mappings if m.user_confirmed and m.onet_code]

        if not confirmed:
            return {
                "session_id": str(session_id),
                "overall_summary": {
                    "total_tasks": 0,
                    "selected_count": 0,
                    "occupation_count": 0,
                    "total_employees": 0,
                },
                "lob_groups": [],
                "ungrouped_occupations": [],
            }

        # Get all task selections for session
        selections = await self.selection_repository.get_for_session(session_id)

        # Build mapping lookup: role_mapping_id -> mapping info
        mapping_lookup = {
            str(m.id): {
                "onet_code": m.onet_code,
                "onet_title": m.onet_title,
                "source_role": m.source_role,
                "lob": m.lob_value,
                "employee_count": m.row_count or 0,
            }
            for m in confirmed
        }

        # Group tasks by role_mapping_id first
        tasks_by_mapping: dict[str, list[dict[str, Any]]] = {}
        for s in selections:
            mapping_id = str(s.role_mapping_id)
            if mapping_id not in mapping_lookup:
                continue  # Skip tasks for unconfirmed mappings
            if mapping_id not in tasks_by_mapping:
                tasks_by_mapping[mapping_id] = []
            tasks_by_mapping[mapping_id].append({
                "id": str(s.id),
                "role_mapping_id": mapping_id,
                "task_id": s.task_id,
                "description": s.task.description if s.task else None,
                "importance": s.task.importance if s.task else None,
                "selected": s.selected,
                "user_modified": s.user_modified,
            })

        # Group by LOB -> O*NET code
        # Structure: {lob: {onet_code: OnetTaskGroup}}
        lob_to_occupations: dict[str | None, dict[str, dict[str, Any]]] = {}

        for mapping_id, info in mapping_lookup.items():
            lob = info["lob"]
            onet_code = info["onet_code"]
            onet_title = info["onet_title"]

            if lob not in lob_to_occupations:
                lob_to_occupations[lob] = {}

            if onet_code not in lob_to_occupations[lob]:
                # First mapping with this O*NET code in this LOB
                lob_to_occupations[lob][onet_code] = {
                    "onet_code": onet_code,
                    "onet_title": onet_title or "Unknown",
                    "role_mapping_ids": [mapping_id],
                    "source_roles": [info["source_role"]],
                    "employee_count": info["employee_count"],
                    "tasks": tasks_by_mapping.get(mapping_id, []),
                }
            else:
                # Additional mapping with same O*NET code - aggregate
                existing = lob_to_occupations[lob][onet_code]
                existing["role_mapping_ids"].append(mapping_id)
                existing["source_roles"].append(info["source_role"])
                existing["employee_count"] += info["employee_count"]
                # Tasks are the same for same O*NET code, so we use first occurrence

        # Build LOB groups and calculate summaries
        lob_groups = []
        ungrouped_occupations = []
        overall_total_tasks = 0
        overall_selected_count = 0
        overall_occupation_count = 0
        overall_total_employees = 0

        for lob, occupations_dict in sorted(
            lob_to_occupations.items(),
            key=lambda x: (x[0] is None, x[0] or ""),  # None goes last
        ):
            occupation_list = list(occupations_dict.values())

            # Calculate group summary
            group_total_tasks = sum(len(occ["tasks"]) for occ in occupation_list)
            group_selected_count = sum(
                sum(1 for t in occ["tasks"] if t["selected"])
                for occ in occupation_list
            )
            group_occupation_count = len(occupation_list)
            group_total_employees = sum(
                occ["employee_count"] for occ in occupation_list
            )

            # Update overall totals
            overall_total_tasks += group_total_tasks
            overall_selected_count += group_selected_count
            overall_occupation_count += group_occupation_count
            overall_total_employees += group_total_employees

            if lob is None:
                # No LOB - add to ungrouped
                ungrouped_occupations.extend(occupation_list)
            else:
                lob_groups.append({
                    "lob": lob,
                    "summary": {
                        "total_tasks": group_total_tasks,
                        "selected_count": group_selected_count,
                        "occupation_count": group_occupation_count,
                        "total_employees": group_total_employees,
                    },
                    "occupations": occupation_list,
                })

        return {
            "session_id": str(session_id),
            "overall_summary": {
                "total_tasks": overall_total_tasks,
                "selected_count": overall_selected_count,
                "occupation_count": overall_occupation_count,
                "total_employees": overall_total_employees,
            },
            "lob_groups": lob_groups,
            "ungrouped_occupations": ungrouped_occupations,
        }

    async def bulk_update_by_onet_code(
        self,
        session_id: UUID,
        onet_code: str,
        selected: bool,
        lob: str | None = None,
    ) -> dict[str, int]:
        """Bulk update task selections for all mappings with a given O*NET code.

        When multiple role mappings share the same O*NET code (within a LOB),
        this updates tasks across all of them at once.

        Args:
            session_id: Discovery session ID.
            onet_code: O*NET occupation code.
            selected: New selection status.
            lob: Optional LOB filter. If provided, only updates mappings in this LOB.

        Returns:
            Dict with updated count.
        """
        if not self.role_mapping_repository:
            return {"updated_count": 0}

        # Get mappings with this O*NET code
        mappings = await self.role_mapping_repository.get_for_session(session_id)
        target_mappings = [
            m for m in mappings
            if m.user_confirmed
            and m.onet_code == onet_code
            and (lob is None or m.lob_value == lob)
        ]

        if not target_mappings:
            return {"updated_count": 0}

        # Collect all mapping IDs and update in a single query
        mapping_ids = [m.id for m in target_mappings]
        total_updated = await self.selection_repository.bulk_update_by_role_mapping_ids(
            mapping_ids, selected
        )

        return {"updated_count": total_updated}

    async def get_selection_stats(
        self,
        session_id: UUID,
    ) -> dict[str, int]:
        """Get selection count statistics for a session.

        Args:
            session_id: Discovery session ID.

        Returns:
            Dict with total, selected, and unselected counts.
        """
        selections = list(await self.selection_repository.get_for_session(session_id))
        total = len(selections)
        selected = sum(1 for s in selections if s.selected)

        return {
            "total": total,
            "selected": selected,
            "unselected": total - selected,
        }

    async def get_selected_tasks_with_dwas(
        self,
        session_id: UUID,
    ) -> list[dict[str, Any]]:
        """Get selected tasks with their associated DWAs for AI analysis.

        This method provides the Task → DWA mapping needed for AI impact
        analysis through the DWA → IWA → GWA hierarchy.

        Args:
            session_id: Discovery session ID.

        Returns:
            List of dicts with task info and associated DWA IDs.
        """
        if not self.onet_repository:
            return []

        selections = await self.selection_repository.get_for_session(session_id)
        selected = [s for s in selections if s.selected]

        if not selected:
            return []

        # Get task IDs
        task_ids = [s.task_id for s in selected]

        # Get DWA mappings for these tasks
        task_to_dwas = await self.onet_repository.get_dwas_for_tasks(task_ids)

        # Build selection lookup
        selection_lookup = {s.task_id: s for s in selected}

        results = []
        for task_id, dwa_ids in task_to_dwas.items():
            selection = selection_lookup.get(task_id)
            if selection and selection.task:
                results.append({
                    "task_id": task_id,
                    "description": selection.task.description,
                    "importance": selection.task.importance,
                    "dwa_ids": dwa_ids,
                })

        return results


async def get_task_service() -> AsyncGenerator[TaskService, None]:
    """Get task service dependency for FastAPI.

    Yields a fully configured TaskService with selection, O*NET, and role mapping repositories.
    """
    from app.models.base import async_session_maker

    async with async_session_maker() as db:
        selection_repository = TaskSelectionRepository(db)
        onet_repository = OnetRepository(db)
        role_mapping_repository = RoleMappingRepository(db)
        service = TaskService(
            selection_repository=selection_repository,
            onet_repository=onet_repository,
            role_mapping_repository=role_mapping_repository,
        )
        yield service
