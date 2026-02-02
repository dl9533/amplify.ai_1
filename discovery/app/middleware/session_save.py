# discovery/app/middleware/session_save.py
"""Session auto-save middleware."""
import logging
from typing import Any
from uuid import UUID

from app.services.session_service import SessionService

logger = logging.getLogger(__name__)


class AutoSaveMiddleware:
    """Middleware for automatic session state persistence.

    Saves session state after each successful interaction
    to enable recovery from failures.
    """

    def __init__(self, session_service: SessionService) -> None:
        self.session_service = session_service
        self._pending_saves: dict[UUID, dict[str, Any]] = {}

    async def save_session_state(
        self,
        session_id: UUID,
        state: dict[str, Any],
    ) -> None:
        """Save session state to database.

        Args:
            session_id: Session to save.
            state: State data to persist.
        """
        try:
            # Get current session
            session = await self.session_service.get_by_id(session_id)
            if not session:
                logger.warning(f"Session {session_id} not found for auto-save")
                return

            # Update step if changed
            if "current_step" in state:
                await self.session_service.update_step(
                    session_id, state["current_step"]
                )

            logger.debug(f"Auto-saved session {session_id}")

        except Exception as e:
            logger.error(f"Failed to auto-save session {session_id}: {e}")

    def queue_save(self, session_id: UUID, state: dict[str, Any]) -> None:
        """Queue a session save for batch processing."""
        self._pending_saves[session_id] = state

    async def flush_pending_saves(self) -> int:
        """Flush all pending saves.

        Returns:
            Number of sessions saved.
        """
        count = 0
        for session_id, state in list(self._pending_saves.items()):
            await self.save_session_state(session_id, state)
            del self._pending_saves[session_id]
            count += 1
        return count
