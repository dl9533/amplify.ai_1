"""Base subagent class for the Discovery service."""
from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseSubagent(ABC):
    """Abstract base class for all subagents in the Discovery service.

    Attributes:
        agent_type: The type identifier for this agent (must be defined in subclasses).
        mcp_enabled: Whether Model Context Protocol is enabled (default: False).
        a2a_enabled: Whether Agent-to-Agent communication is enabled (default: False).
        a2ui_enabled: Whether Agent-to-UI communication is enabled (default: False).
    """

    agent_type: str
    mcp_enabled: bool = False
    a2a_enabled: bool = False
    a2ui_enabled: bool = False

    def __init__(self, session: Any, memory_service: Any) -> None:
        """Initialize the subagent.

        Args:
            session: Database session for persistence operations.
            memory_service: Service for agent memory management.
        """
        self.session = session
        self.memory_service = memory_service

    @abstractmethod
    async def process(self, message: str) -> Any:
        """Process an incoming message and return a response.

        Args:
            message: The input message to process.

        Returns:
            The processed response.
        """
        pass

    def format_response(
        self,
        message: str,
        choices: Optional[list[str]] = None,
        **kwargs: Any
    ) -> dict[str, Any]:
        """Format a response with brainstorming style.

        Args:
            message: The response message.
            choices: Optional list of choices to present.
            **kwargs: Additional response metadata.

        Returns:
            A structured response dictionary.
        """
        response: dict[str, Any] = {
            "message": message,
            "agent_type": self.agent_type,
        }

        if choices is not None:
            response["choices"] = choices

        response.update(kwargs)

        return response
