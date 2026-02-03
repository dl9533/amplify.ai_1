"""Chat services for the Discovery module."""

import json
import logging
from collections.abc import AsyncGenerator, AsyncIterator
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.models.base import async_session_maker
from app.repositories.chat_message_repository import ChatMessageRepository
from app.services.context_service import ContextService, get_context_service
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

# Action handlers mapping
ACTION_RESPONSES: dict[str, dict[str, Any]] = {
    "upload_file": {
        "response": "Please use the file upload button above to upload your workforce data file (CSV or Excel format).",
        "data": {"action_type": "ui_prompt", "target": "file_upload"},
    },
    "view_sample_format": {
        "response": "The expected format includes columns for: Role/Job Title, Department, Location, and Employee Count. You can download a sample template from the help section.",
        "data": {"action_type": "info"},
    },
    "confirm_all_mappings": {
        "response": "I'll confirm all role mappings with high confidence scores (85%+). You can still review and adjust individual mappings.",
        "data": {"action_type": "bulk_action", "threshold": 0.85},
    },
    "search_onet": {
        "response": "Click on any role to search for alternative O*NET occupation matches.",
        "data": {"action_type": "ui_prompt", "target": "onet_search"},
    },
    "select_high_exposure": {
        "response": "I'll select all activities with high AI exposure scores. These represent the best opportunities for automation.",
        "data": {"action_type": "bulk_select", "filter": "high_exposure"},
    },
    "clear_selections": {
        "response": "All activity selections have been cleared. You can start fresh.",
        "data": {"action_type": "clear"},
    },
    "view_by_role": {
        "response": "Switching to role-based view of analysis results.",
        "data": {"action_type": "view_change", "dimension": "role"},
    },
    "view_by_department": {
        "response": "Switching to department-based view of analysis results.",
        "data": {"action_type": "view_change", "dimension": "department"},
    },
    "add_to_now": {
        "response": "Select items from the analysis to add to the NOW phase of your roadmap.",
        "data": {"action_type": "ui_prompt", "target": "roadmap_add"},
    },
    "export_roadmap": {
        "response": "Your roadmap is being prepared for export. You can download it as PDF or Excel.",
        "data": {"action_type": "export", "formats": ["pdf", "xlsx"]},
    },
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
        chat_message_repository: ChatMessageRepository | None = None,
    ) -> None:
        """Initialize the chat service.

        Args:
            llm_service: The LLM service for generating responses.
            context_service: The context service for building session context.
            chat_message_repository: Optional repository for persisting messages.
        """
        self.llm_service = llm_service
        self.context_service = context_service
        self.chat_message_repository = chat_message_repository

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
        # Save user message if repository available
        if self.chat_message_repository:
            await self.chat_message_repository.create(
                session_id=session_id,
                role="user",
                content=message,
            )

        # Get session context from ContextService
        context = await self.context_service.build_context(
            session_id=session_id,
            current_step=current_step,
            user_message=message,
        )

        # Build system prompt based on context
        system_prompt = self._build_system_prompt(context)

        # Get conversation history from DB if not provided
        if conversation_history is None and self.chat_message_repository:
            history_messages = await self.chat_message_repository.get_for_session(
                session_id, limit=20
            )
            # Convert to format expected by LLM (exclude last message which is current)
            conversation_history = [
                {"role": m.role, "content": m.content}
                for m in history_messages[:-1]  # Exclude last (current) message
            ]

        # Call LLM to generate response
        response = await self.llm_service.generate_response(
            system_prompt=system_prompt,
            user_message=message,
            conversation_history=conversation_history,
        )

        # Save assistant response if repository available
        if self.chat_message_repository:
            await self.chat_message_repository.create(
                session_id=session_id,
                role="assistant",
                content=response,
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
        """
        if not self.chat_message_repository:
            # Return empty history if no repository configured
            return []

        messages = await self.chat_message_repository.get_for_session(session_id)

        return [
            {
                "role": m.role,
                "content": m.content,
                "timestamp": m.created_at.isoformat(),
            }
            for m in messages
        ]

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
            Dict with response and data, or None if action not found.
            Contains: response (str), data (dict).
        """
        # Check if action exists in predefined responses
        if action in ACTION_RESPONSES:
            action_config = ACTION_RESPONSES[action]
            return {
                "response": action_config["response"],
                "data": {**action_config["data"], "params": params},
            }

        # Unknown action - provide generic response
        return {
            "response": f"Action '{action}' is not recognized. Please try a different action.",
            "data": {"action_type": "error", "action": action},
        }

    async def stream_response(
        self,
        session_id: UUID,
        message: str | None = None,
        current_step: int = 1,
    ) -> Optional[AsyncIterator[str]]:
        """Stream responses for a session via SSE.

        Args:
            session_id: The session ID to stream responses for.
            message: Optional message to respond to (uses last message if not provided).
            current_step: Current step in the discovery process.

        Returns:
            AsyncIterator yielding SSE-formatted strings.
        """
        # Get context for system prompt
        user_message = message or "Continue helping me with the discovery process."

        context = await self.context_service.build_context(
            session_id=session_id,
            current_step=current_step,
            user_message=user_message,
        )

        system_prompt = self._build_system_prompt(context)

        # Get conversation history
        conversation_history = None
        if self.chat_message_repository:
            history_messages = await self.chat_message_repository.get_for_session(
                session_id, limit=20
            )
            conversation_history = [
                {"role": m.role, "content": m.content}
                for m in history_messages
            ]

        async def sse_generator() -> AsyncIterator[str]:
            """Generate SSE-formatted events."""
            full_response = ""
            try:
                async for chunk in self.llm_service.stream_response(
                    system_prompt=system_prompt,
                    user_message=user_message,
                    conversation_history=conversation_history,
                ):
                    full_response += chunk
                    # Format as SSE event
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"

                # Send completion event
                yield f"data: {json.dumps({'type': 'done', 'content': full_response})}\n\n"

                # Save the full response to history
                if self.chat_message_repository and message:
                    await self.chat_message_repository.create(
                        session_id=session_id,
                        role="user",
                        content=message,
                    )
                    await self.chat_message_repository.create(
                        session_id=session_id,
                        role="assistant",
                        content=full_response,
                    )

            except Exception as e:
                logger.error(f"Error streaming response: {e}")
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

        return sse_generator()


async def get_chat_service() -> AsyncGenerator[ChatService, None]:
    """Dependency to get chat service.

    Creates LLMService, ContextService, and ChatMessageRepository,
    then injects them into ChatService.

    Yields:
        A ChatService instance with all dependencies configured.
    """
    settings = get_settings()
    llm_service = LLMService(settings=settings)

    async with async_session_maker() as db:
        context_service = await get_context_service(db)
        chat_message_repository = ChatMessageRepository(db)
        yield ChatService(
            llm_service=llm_service,
            context_service=context_service,
            chat_message_repository=chat_message_repository,
        )
