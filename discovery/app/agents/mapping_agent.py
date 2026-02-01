"""Mapping Subagent for O*NET occupation matching."""
from typing import Any, Optional
from uuid import UUID

from app.agents.base import BaseSubagent


class MappingSubagent(BaseSubagent):
    """Subagent for matching source roles to O*NET occupations.

    This agent handles the O*NET occupation matching process using a
    brainstorming-style interaction. It suggests O*NET matches for
    source roles and allows users to confirm or search for alternatives.

    Attributes:
        agent_type: The type identifier for this agent ('mapping').
        _confirmed_mappings: Dictionary of confirmed role mappings.
        _onet_repo: Repository for O*NET occupation searches.
        _current_role: The current role being mapped.
        _pending_role_id: ID of a role pending user confirmation.
    """

    agent_type: str = "mapping"

    def __init__(self, session: Any, memory_service: Any) -> None:
        """Initialize the MappingSubagent.

        Args:
            session: Database session for persistence operations.
            memory_service: Service for agent memory management.
        """
        super().__init__(session, memory_service)
        self._confirmed_mappings: dict[str, str] = {}
        self._onet_repo: Optional[Any] = None
        self._current_role: Optional[Any] = None
        self._pending_role_id: Optional[UUID] = None

    async def suggest_matches(
        self,
        source_role: str,
        onet_repo: Any,
        limit: int = 5,
    ) -> list[Any]:
        """Suggest O*NET occupations for a source role.

        Args:
            source_role: The source role title to match.
            onet_repo: Repository for O*NET occupation searches.
            limit: Maximum number of suggestions to return.

        Returns:
            A list of O*NET occupation matches with scores.
        """
        results = await onet_repo.search_occupations(
            query=source_role,
            limit=limit,
        )
        return results

    async def confirm_mapping(
        self,
        role_mapping_id: UUID,
        onet_code: str,
        confidence: float,
    ) -> None:
        """Store a confirmed role mapping.

        Args:
            role_mapping_id: The unique ID of the role mapping.
            onet_code: The O*NET occupation code selected.
            confidence: The confidence score for this mapping.
        """
        self._confirmed_mappings[str(role_mapping_id)] = onet_code

    async def process(self, message: str) -> dict[str, Any]:
        """Process an incoming message and return a response.

        Implements a brainstorming-style interaction where the agent
        presents O*NET matches and handles user selections.

        Args:
            message: The input message to process.

        Returns:
            A structured response dictionary with message/question and choices.
        """
        message_lower = message.lower()

        # Handle "none of these" selection
        if "none" in message_lower and (
            "these" in message_lower or "match" in message_lower
        ):
            return self.format_response(
                message="No problem! Let's search for a better match.",
                question="Please specify the role or search for a custom O*NET code.",
                choices=["Search by keyword", "Enter O*NET code directly"],
            )

        # If we have a current role, present O*NET matches
        if self._current_role is not None and self._onet_repo is not None:
            matches = await self.suggest_matches(
                source_role=self._current_role.source_role,
                onet_repo=self._onet_repo,
                limit=5,
            )

            choices = [f"{m.code} - {m.title}" for m in matches]
            choices.append("None of these")

            return self.format_response(
                message=f"I found these O*NET matches for '{self._current_role.source_role}':",
                question="Which O*NET occupation best matches this role?",
                choices=choices,
            )

        # Default response when no role is being mapped
        return self.format_response(
            message="Ready to map roles to O*NET occupations.",
            question="Which role would you like to map?",
            choices=["Start mapping"],
        )
