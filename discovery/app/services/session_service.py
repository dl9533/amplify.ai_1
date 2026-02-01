"""Session service for managing discovery sessions."""
from typing import Optional
from uuid import UUID

from app.repositories.session_repository import SessionRepository


class SessionService:
    """Session service backed by database repository.

    Manages discovery session lifecycle including creation,
    retrieval, step progression, and deletion.
    """

    def __init__(
        self,
        repository: SessionRepository | None = None,
        user_id: UUID | None = None,
    ) -> None:
        """Initialize with repository dependency.

        Args:
            repository: SessionRepository for database operations.
                If None, methods will raise NotImplementedError.
            user_id: Current user ID for session ownership.
        """
        self.repository = repository
        self.user_id = user_id

    def _require_repository(self) -> SessionRepository:
        """Ensure repository is configured."""
        if self.repository is None:
            raise NotImplementedError(
                "SessionService requires a repository. "
                "Use create_session_service() factory or pass repository to constructor."
            )
        return self.repository

    async def create(self, organization_id: UUID) -> dict:
        """Create a new discovery session.

        Args:
            organization_id: Organization the session belongs to.

        Returns:
            Dict with session data including id, status, current_step.
        """
        repo = self._require_repository()

        if not self.user_id:
            raise ValueError("user_id required to create session")

        session = await repo.create(
            user_id=self.user_id,
            organization_id=organization_id,
        )
        return {
            "id": str(session.id),
            "status": session.status.value,
            "current_step": session.current_step,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat() if session.updated_at else session.created_at.isoformat(),
        }

    async def get_by_id(self, session_id: UUID) -> Optional[dict]:
        """Get a session by ID.

        Args:
            session_id: UUID of the session.

        Returns:
            Session dict or None if not found.
        """
        repo = self._require_repository()

        session = await repo.get_by_id(session_id)
        if not session:
            return None
        return {
            "id": str(session.id),
            "status": session.status.value,
            "current_step": session.current_step,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
        }

    async def list_for_user(
        self,
        page: int = 1,
        per_page: int = 20,
    ) -> dict:
        """List sessions for the current user.

        Args:
            page: Page number (1-indexed).
            per_page: Results per page.

        Returns:
            Dict with sessions list and pagination metadata.
        """
        repo = self._require_repository()

        if not self.user_id:
            raise ValueError("user_id required to list sessions")

        sessions, total = await repo.list_for_user(
            user_id=self.user_id,
            page=page,
            per_page=per_page,
        )
        return {
            "items": [
                {
                    "id": str(s.id),
                    "status": s.status.value,
                    "current_step": s.current_step,
                    "updated_at": s.updated_at.isoformat(),
                }
                for s in sessions
            ],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    async def update_step(self, session_id: UUID, step: int) -> Optional[dict]:
        """Update session step.

        Args:
            session_id: UUID of the session.
            step: New step number (1-5).

        Returns:
            Updated session dict or None if not found.
        """
        repo = self._require_repository()

        session = await repo.update_step(session_id, step)
        if not session:
            return None
        return {
            "id": str(session.id),
            "status": session.status.value,
            "current_step": session.current_step,
        }

    async def delete(self, session_id: UUID) -> bool:
        """Delete a session.

        Args:
            session_id: UUID of the session to delete.

        Returns:
            True if deleted, False if not found.
        """
        repo = self._require_repository()
        return await repo.delete(session_id)


def get_session_service() -> SessionService:
    """Get session service dependency for FastAPI.

    Note: This returns a service without repository configured.
    Use create_session_service() for database-backed service.

    Returns:
        SessionService without repository.
    """
    return SessionService()


def create_session_service(
    repository: SessionRepository,
    user_id: UUID | None = None,
) -> SessionService:
    """Factory function for database-backed session service.

    Args:
        repository: SessionRepository instance.
        user_id: Current authenticated user ID.

    Returns:
        Configured SessionService instance with repository.
    """
    return SessionService(repository=repository, user_id=user_id)
