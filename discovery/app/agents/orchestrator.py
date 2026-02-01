"""Discovery Orchestrator for routing messages to appropriate subagents."""
from typing import Any
from uuid import uuid4

from app.enums import DiscoveryStep


class DiscoveryOrchestrator:
    """Orchestrates the discovery wizard by routing messages to appropriate subagents.

    The orchestrator manages the discovery workflow by:
    - Routing messages to the correct subagent based on current step
    - Advancing through wizard steps when subagents complete
    - Maintaining conversation history and thread management

    Attributes:
        _session: The current discovery session.
        _memory_service: Service for agent memory management.
        _subagents: Dictionary mapping step names to subagent instances.
        _conversation_id: UUID for the current conversation thread.
        _message_history: List of messages in the conversation.
    """

    # Step order for wizard progression
    _STEP_ORDER: list[DiscoveryStep] = [
        DiscoveryStep.UPLOAD,
        DiscoveryStep.MAP_ROLES,
        DiscoveryStep.SELECT_ACTIVITIES,
        DiscoveryStep.ANALYZE,
        DiscoveryStep.ROADMAP,
    ]

    # Mapping from DiscoveryStep to subagent key
    _STEP_TO_SUBAGENT: dict[DiscoveryStep, str] = {
        DiscoveryStep.UPLOAD: "upload",
        DiscoveryStep.MAP_ROLES: "mapping",
        DiscoveryStep.SELECT_ACTIVITIES: "activity",
        DiscoveryStep.ANALYZE: "analysis",
        DiscoveryStep.ROADMAP: "roadmap",
    }

    def __init__(self, session: Any, memory_service: Any) -> None:
        """Initialize the DiscoveryOrchestrator.

        Args:
            session: The discovery session with current_step attribute.
            memory_service: Service for agent memory management.
        """
        self._session = session
        self._memory_service = memory_service
        self._subagents: dict[str, Any] = {}
        self._conversation_id: str = str(uuid4())
        self._message_history: list[dict[str, Any]] = []

    async def process(self, message: str) -> dict[str, Any]:
        """Process an incoming message by routing to the appropriate subagent.

        Routes the message to the subagent responsible for the current step,
        advances to the next step if the subagent indicates completion,
        and maintains conversation history.

        Args:
            message: The input message to process.

        Returns:
            The response from the subagent.
        """
        # Store user message in history
        self._message_history.append({
            "role": "user",
            "content": message,
        })

        # Get the appropriate subagent for the current step
        current_step = self._session.current_step
        subagent_key = self._STEP_TO_SUBAGENT.get(current_step)

        if subagent_key is None or subagent_key not in self._subagents:
            response = {"message": "Unknown step", "step_complete": False}
        else:
            subagent = self._subagents[subagent_key]
            response = await subagent.process(message)

        # Store agent response in history
        self._message_history.append({
            "role": "assistant",
            "content": response.get("message", ""),
        })

        # Advance step if subagent indicates completion
        if response.get("step_complete", False):
            self._advance_step()

        return response

    def _advance_step(self) -> None:
        """Advance to the next step in the wizard workflow."""
        current_step = self._session.current_step
        try:
            current_index = self._STEP_ORDER.index(current_step)
            if current_index < len(self._STEP_ORDER) - 1:
                self._session.current_step = self._STEP_ORDER[current_index + 1]
        except ValueError:
            # Current step not found in order, don't advance
            pass
