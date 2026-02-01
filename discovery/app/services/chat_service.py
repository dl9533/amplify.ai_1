"""Chat services for the Discovery module."""

import json
import logging
from typing import Any, AsyncIterator, Optional
from uuid import UUID

from app.config import Settings, get_settings
from app.services.context_service import ContextService
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

# Quick actions by step
QUICK_ACTIONS_BY_STEP: dict[int, list[dict[str, str]]] = {
    1: [  # Upload
        {"label": "Upload file", "action": "upload_file"},
        {"label": "View sample format", "action": "view_sample_format"},
    ],
    2: [  # Map Roles
        {"label": "Confirm all mappings", "action": "confirm_all_mappings"},
        {"label": "Search O*NET", "action": "search_onet"},
    ],
    3: [  # Select Activities
        {"label": "Select high exposure", "action": "select_high_exposure"},
        {"label": "Clear selections", "action": "clear_selections"},
    ],
    4: [  # Analysis
        {"label": "View by role", "action": "view_by_role"},
        {"label": "View by department", "action": "view_by_department"},
    ],
    5: [  # Roadmap
        {"label": "Add to NOW", "action": "add_to_now"},
        {"label": "Export roadmap", "action": "export_roadmap"},
    ],
}


class ChatService:
    """Chat service for handling chat messages and actions.

    This service integrates with LLMService for AI-powered responses and
    ContextService for session context management.
    """

    def __init__(
        self,
        llm_service: LLMService,
        context_service: ContextService,
    ) -> None:
        """Initialize the chat service.

        Args:
            llm_service: The LLM service for generating responses.
            context_service: The context service for building session context.
        """
        self.llm_service = llm_service
        self.context_service = context_service

    async def send_message(
        self,
        session_id: UUID,
        message: str,
        current_step: int = 1,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        """Send a message to the AI assistant.

        Args:
            session_id: The session ID to send the message for.
            message: The message content to send.
            current_step: The current step in the discovery process (1-5).
            conversation_history: Optional list of previous messages.

        Returns:
            Dict with response and quick_actions.
            Contains: response (str), quick_actions (list of {label, action}).

        Raises:
            LLMAuthError: If LLM authentication fails.
            LLMRateLimitError: If LLM rate limit is exceeded.
            LLMConnectionError: If connection to LLM fails.
            LLMError: For other LLM errors.
            ValueError: If current_step is invalid.
        """
        # Get session context from ContextService
        context = self.context_service.build_context(
            session_id=session_id,
            current_step=current_step,
            user_message=message,
        )

        # Build system prompt based on context
        system_prompt = self._build_system_prompt(context)

        # Call LLM to generate response
        response = await self.llm_service.generate_response(
            system_prompt=system_prompt,
            user_message=message,
            conversation_history=conversation_history,
        )

        # Get quick actions for the current step
        quick_actions = self._get_quick_actions(current_step)

        return {
            "response": response,
            "quick_actions": quick_actions,
        }

    def _build_system_prompt(self, context: dict[str, Any]) -> str:
        """Build the system prompt based on session context.

        Args:
            context: The session context from ContextService.

        Returns:
            The system prompt string.
        """
        step_name = context.get("step_name", "Unknown")

        # Extract session data (excluding non-serializable or meta fields)
        session_data: dict[str, Any] = {}
        exclude_keys = {"current_step", "step_name", "session_id", "suggested_actions"}
        for key, value in context.items():
            if key not in exclude_keys:
                session_data[key] = value

        return f"""You are a Discovery assistant helping users identify AI automation opportunities.

Current step: {step_name}
Session data: {json.dumps(session_data)}

Help the user complete this step of the discovery process."""

    def _get_quick_actions(self, current_step: int) -> list[dict[str, str]]:
        """Get quick actions for the current step.

        Args:
            current_step: The current step number (1-5).

        Returns:
            List of quick action dictionaries with label and action keys.
        """
        return QUICK_ACTIONS_BY_STEP.get(current_step, [])

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
    """Dependency to get chat service.

    Creates LLMService and ContextService, then injects them into ChatService.

    Returns:
        A ChatService instance with all dependencies configured.
    """
    settings = get_settings()
    llm_service = LLMService(settings=settings)
    context_service = ContextService()
    return ChatService(
        llm_service=llm_service,
        context_service=context_service,
    )
