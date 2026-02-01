"""Roadmap services for the Discovery module."""
from typing import Optional
from uuid import UUID

from app.schemas.roadmap import BulkPhaseUpdate, RoadmapPhase


class RoadmapService:
    """Roadmap service for managing roadmap items.

    This is a placeholder service that will be replaced with actual
    database operations in a later task.
    """

    async def get_roadmap(
        self,
        session_id: UUID,
        phase: Optional[RoadmapPhase] = None,
    ) -> Optional[list[dict]]:
        """Get roadmap items for a session.

        Args:
            session_id: The session ID to get roadmap items for.
            phase: Optional phase filter (NOW, NEXT, LATER).

        Returns:
            List of roadmap item dicts, or None if session not found.
            Each item contains: id, role_name, priority_score, priority_tier,
            phase, estimated_effort, and order.

        Raises:
            NotImplementedError: Service not implemented.
        """
        raise NotImplementedError("Service not implemented")

    async def update_phase(
        self,
        item_id: UUID,
        phase: RoadmapPhase,
    ) -> Optional[dict]:
        """Update a roadmap item's phase.

        Args:
            item_id: The roadmap item ID to update.
            phase: The new phase to set.

        Returns:
            Updated roadmap item dict, or None if item not found.

        Raises:
            NotImplementedError: Service not implemented.
        """
        raise NotImplementedError("Service not implemented")

    async def reorder(
        self,
        session_id: UUID,
        item_ids: list[UUID],
    ) -> Optional[bool]:
        """Reorder roadmap items within a session.

        Args:
            session_id: The session ID.
            item_ids: Ordered list of roadmap item IDs.

        Returns:
            True if successful, None if session not found.

        Raises:
            NotImplementedError: Service not implemented.
        """
        raise NotImplementedError("Service not implemented")

    async def bulk_update(
        self,
        session_id: UUID,
        updates: list[BulkPhaseUpdate],
    ) -> Optional[int]:
        """Bulk update phases for multiple roadmap items.

        Args:
            session_id: The session ID.
            updates: List of BulkPhaseUpdate items with id and phase.

        Returns:
            Number of items updated, or None if session not found.

        Raises:
            NotImplementedError: Service not implemented.
        """
        raise NotImplementedError("Service not implemented")


def get_roadmap_service() -> RoadmapService:
    """Dependency to get roadmap service."""
    return RoadmapService()
