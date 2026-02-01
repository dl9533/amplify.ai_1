"""Session service for managing discovery sessions."""
from typing import Optional
from uuid import UUID


class SessionService:
    """Session service for managing discovery sessions.

    This is a placeholder service that will be replaced with actual
    database operations in a later task.
    """

    async def create(self, organization_id: UUID) -> dict:
        """Create a new discovery session."""
        raise NotImplementedError("Service not implemented")

    async def get_by_id(self, session_id: UUID) -> Optional[dict]:
        """Get a session by ID."""
        raise NotImplementedError("Service not implemented")

    async def list_for_user(
        self,
        page: int = 1,
        per_page: int = 20,
    ) -> dict:
        """List sessions for the current user."""
        raise NotImplementedError("Service not implemented")

    async def update_step(self, session_id: UUID, step: int) -> Optional[dict]:
        """Update session step."""
        raise NotImplementedError("Service not implemented")

    async def delete(self, session_id: UUID) -> bool:
        """Delete a session."""
        raise NotImplementedError("Service not implemented")


def get_session_service() -> SessionService:
    """Dependency to get session service."""
    return SessionService()
