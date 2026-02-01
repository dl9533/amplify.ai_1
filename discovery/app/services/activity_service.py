"""Activity service for managing activity selections."""
from typing import Optional
from uuid import UUID


class ActivityService:
    """Activity service for managing activity selections.

    This is a placeholder service that will be replaced with actual
    database operations in a later task.
    """

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
            List of GWA groups with their DWAs, or None if session not found.

        Raises:
            NotImplementedError: Service not implemented.
        """
        raise NotImplementedError("Service not implemented")

    async def update_selection(
        self,
        activity_id: UUID,
        selected: bool,
    ) -> Optional[dict]:
        """Update the selection status of a single activity.

        Args:
            activity_id: The activity ID to update.
            selected: The new selection status.

        Returns:
            Updated activity data, or None if activity not found.

        Raises:
            NotImplementedError: Service not implemented.
        """
        raise NotImplementedError("Service not implemented")

    async def bulk_update_selection(
        self,
        session_id: UUID,
        activity_ids: list[UUID],
        selected: bool,
    ) -> Optional[dict]:
        """Bulk update selection status for multiple activities.

        Args:
            session_id: The session ID the activities belong to.
            activity_ids: List of activity IDs to update.
            selected: The new selection status for all activities.

        Returns:
            Dict with updated_count, or None if session not found.

        Raises:
            NotImplementedError: Service not implemented.
        """
        raise NotImplementedError("Service not implemented")

    async def get_selection_count(
        self,
        session_id: UUID,
    ) -> Optional[dict]:
        """Get selection count statistics for a session.

        Args:
            session_id: The session ID to get counts for.

        Returns:
            Dict with total, selected, and unselected counts,
            or None if session not found.

        Raises:
            NotImplementedError: Service not implemented.
        """
        raise NotImplementedError("Service not implemented")


def get_activity_service() -> ActivityService:
    """Dependency to get activity service."""
    return ActivityService()
