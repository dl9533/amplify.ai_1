"""Chat services for the Discovery module."""
from typing import Any, AsyncIterator, Optional
from uuid import UUID


class ChatService:
    """Chat service for handling chat messages and actions.

    This is a placeholder service that will be replaced with actual
    orchestrator integration in a later task.
    """

    async def send_message(
        self,
        session_id: UUID,
        message: str,
    ) -> Optional[dict]:
        """Send a message to the orchestrator.

        Args:
            session_id: The session ID to send the message for.
            message: The message content to send.

        Returns:
            Dict with response and quick_actions, or None if session not found.
            Contains: response (str), quick_actions (list of {label, action}).

        Raises:
            NotImplementedError: Service not implemented.
        """
        raise NotImplementedError("Service not implemented")

    async def get_history(
        self,
        session_id: UUID,
    ) -> Optional[list[dict]]:
        """Get chat history for a session.

        Args:
            session_id: The session ID to get history for.

        Returns:
            List of message dicts, or None if session not found.
            Each item contains: role (str), content (str), timestamp (str).

        Raises:
            NotImplementedError: Service not implemented.
        """
        raise NotImplementedError("Service not implemented")

    async def execute_action(
        self,
        session_id: UUID,
        action: str,
        params: dict[str, Any],
    ) -> Optional[dict]:
        """Execute a quick action.

        Args:
            session_id: The session ID.
            action: The action identifier to execute.
            params: Parameters for the action.

        Returns:
            Dict with response and data, or None if session not found.
            Contains: response (str), data (dict).

        Raises:
            NotImplementedError: Service not implemented.
        """
        raise NotImplementedError("Service not implemented")

    async def stream_response(
        self,
        session_id: UUID,
    ) -> Optional[AsyncIterator[str]]:
        """Stream responses for a session via SSE.

        Args:
            session_id: The session ID to stream responses for.

        Returns:
            AsyncIterator yielding SSE-formatted strings, or None if session not found.

        Raises:
            NotImplementedError: Service not implemented.
        """
        raise NotImplementedError("Service not implemented")


def get_chat_service() -> ChatService:
    """Dependency to get chat service."""
    return ChatService()
