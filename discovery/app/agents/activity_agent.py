"""Activity Subagent for DWA (Detailed Work Activity) selection."""
from typing import Any, Optional
from uuid import UUID

from app.agents.base import BaseSubagent


class ActivitySubagent(BaseSubagent):
    """Subagent for DWA selection for mapped O*NET occupations.

    This agent handles the DWA selection process using a brainstorming-style
    interaction. It presents DWAs for O*NET occupations and allows users
    to select relevant activities.

    Attributes:
        agent_type: The type identifier for this agent ('activity').
        _selections: Dictionary of DWA selection states keyed by (role_mapping_id, dwa_id).
        _dwa_repo: Repository for DWA data access.
        _current_dwas: List of DWAs currently being processed.
        _current_dwa_index: Index of the current DWA in brainstorming flow.
    """

    agent_type: str = "activity"

    def __init__(self, session: Any, memory_service: Any) -> None:
        """Initialize the ActivitySubagent.

        Args:
            session: Database session for persistence operations.
            memory_service: Service for agent memory management.
        """
        super().__init__(session, memory_service)
        self._selections: dict[tuple[str, str], bool] = {}
        self._dwa_repo: Optional[Any] = None
        self._current_dwas: list[Any] = []
        self._current_dwa_index: int = 0

    async def get_dwas_for_role(self, onet_code: str) -> list[Any]:
        """Retrieve DWAs for a mapped O*NET occupation.

        Args:
            onet_code: The O*NET occupation code.

        Returns:
            A list of DWAs associated with the occupation.
        """
        if self._dwa_repo is None:
            return []

        dwas = await self._dwa_repo.get_by_occupation(onet_code)
        self._current_dwas = dwas
        return dwas

    async def toggle_dwa(
        self,
        role_mapping_id: UUID,
        dwa_id: str,
        selected: bool,
    ) -> None:
        """Toggle the selection state of a DWA.

        Args:
            role_mapping_id: The unique ID of the role mapping.
            dwa_id: The DWA identifier.
            selected: Whether the DWA is selected.
        """
        self._selections[(str(role_mapping_id), dwa_id)] = selected

    async def select_above_threshold(
        self,
        role_mapping_id: UUID,
        threshold: float,
    ) -> None:
        """Bulk select DWAs with exposure above threshold.

        Args:
            role_mapping_id: The unique ID of the role mapping.
            threshold: The minimum exposure threshold for selection.
        """
        for dwa in self._current_dwas:
            if dwa.gwa_exposure >= threshold:
                self._selections[(str(role_mapping_id), dwa.id)] = True

    async def process(self, message: str) -> dict[str, Any]:
        """Process an incoming message and return a response.

        Implements a brainstorming-style interaction where the agent
        presents DWAs one at a time for relevance confirmation.

        Args:
            message: The input message to process.

        Returns:
            A structured response dictionary with message/question and choices.
        """
        # If we have DWAs to process, present the current one
        if self._current_dwas and self._current_dwa_index < len(self._current_dwas):
            current_dwa = self._current_dwas[self._current_dwa_index]

            return self.format_response(
                message=f"Is this activity relevant to the role?",
                question=f"Activity: {current_dwa.name}",
                choices=["Yes, relevant", "No, not relevant", "Skip"],
                dwa_id=current_dwa.id,
                dwa_name=current_dwa.name,
            )

        # Default response when no DWAs are loaded
        return self.format_response(
            message="Ready to select DWAs for O*NET occupations.",
            question="Would you like to start activity selection?",
            choices=["Start selection"],
        )
