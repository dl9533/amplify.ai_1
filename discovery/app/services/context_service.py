"""Context service for chat-UI coordination."""
from typing import Any
from uuid import UUID


# Step names mapping
STEP_NAMES: dict[int, str] = {
    1: "Upload",
    2: "Map Roles",
    3: "Select Activities",
    4: "Analysis",
    5: "Roadmap",
}


def get_context_service() -> "ContextService":
    """Dependency injection for ContextService."""
    return ContextService()


class ContextService:
    """Service for building context for chat-UI coordination.

    This service provides context information based on the current step
    in the discovery workflow, enabling the chat interface to understand
    the user's current position and provide relevant suggestions.
    """

    def __init__(self) -> None:
        """Initialize the context service."""
        self.step_names = STEP_NAMES

    def build_context(
        self,
        session_id: UUID,
        current_step: int,
        user_message: str,
    ) -> dict[str, Any]:
        """Build context dictionary for the current session state.

        Args:
            session_id: The unique session identifier.
            current_step: The current step number (1-5).
            user_message: The user's message to analyze for context.

        Returns:
            Dictionary containing context information including:
            - current_step: The step number
            - step_name: Human readable step name
            - activities: Activity data (for step 3)
            - selection_count: Number of selections (for step 3)
            - analysis_summary: Analysis results (for step 4+)
            - suggested_actions: Relevant quick actions
        """
        context: dict[str, Any] = {
            "current_step": current_step,
            "step_name": self.step_names.get(current_step, "Unknown"),
            "session_id": str(session_id),
        }

        # Add step-specific data
        if current_step == 3:
            context["activities"] = self._get_activities_data(session_id)
            context["selection_count"] = self._get_selection_count(session_id)

        if current_step >= 4:
            context["analysis_summary"] = self._get_analysis_summary(session_id)

        # Add suggested actions based on context
        context["suggested_actions"] = self._get_suggested_actions(
            current_step, user_message
        )

        return context

    def _get_activities_data(self, session_id: UUID) -> dict[str, Any]:
        """Get activities data for step 3.

        Args:
            session_id: The session identifier.

        Returns:
            Dictionary containing activity groups and data.
        """
        # Mock data for activities - in production this would query the database
        return {
            "gwa_groups": [
                {"id": "gwa_1", "name": "Information Processing", "count": 12},
                {"id": "gwa_2", "name": "Communication", "count": 8},
                {"id": "gwa_3", "name": "Analysis", "count": 15},
            ],
            "total_activities": 35,
        }

    def _get_selection_count(self, session_id: UUID) -> int:
        """Get the count of selected activities.

        Args:
            session_id: The session identifier.

        Returns:
            Number of selected activities.
        """
        # Mock count - in production this would query the database
        return 10

    def _get_analysis_summary(self, session_id: UUID) -> dict[str, Any]:
        """Get analysis summary for step 4+.

        Args:
            session_id: The session identifier.

        Returns:
            Dictionary containing analysis summary with top priorities.
        """
        # Mock analysis summary - in production this would query analysis results
        return {
            "top_priorities": [
                {
                    "id": "priority_1",
                    "name": "Data Analysis Automation",
                    "score": 0.92,
                },
                {
                    "id": "priority_2",
                    "name": "Report Generation",
                    "score": 0.87,
                },
                {
                    "id": "priority_3",
                    "name": "Customer Communication",
                    "score": 0.81,
                },
            ],
            "total_opportunities": 15,
            "high_impact_count": 5,
        }

    def _get_suggested_actions(
        self, current_step: int, user_message: str
    ) -> list[dict[str, Any]]:
        """Get suggested quick actions based on context.

        Args:
            current_step: The current step number.
            user_message: The user's message to analyze.

        Returns:
            List of suggested action dictionaries.
        """
        actions: list[dict[str, Any]] = []

        # Analyze message for keywords and suggest relevant actions
        message_lower = user_message.lower()

        if current_step == 2:
            # Map Roles step
            if any(
                keyword in message_lower
                for keyword in ["not sure", "unsure", "wrong", "change", "different"]
            ):
                actions.append(
                    {
                        "action": "remap_role",
                        "label": "Change Role Mapping",
                        "description": "Select a different O*NET role for this position",
                    }
                )
            actions.append(
                {
                    "action": "view_alternatives",
                    "label": "View Alternative Mappings",
                    "description": "See other possible role mappings",
                }
            )

        elif current_step == 3:
            # Select Activities step
            actions.append(
                {
                    "action": "select_all_category",
                    "label": "Select All in Category",
                    "description": "Select all activities in a category",
                }
            )
            actions.append(
                {
                    "action": "clear_selections",
                    "label": "Clear All Selections",
                    "description": "Remove all selected activities",
                }
            )

        elif current_step == 4:
            # Analysis step
            actions.append(
                {
                    "action": "export_analysis",
                    "label": "Export Analysis",
                    "description": "Download the analysis results",
                }
            )
            actions.append(
                {
                    "action": "refine_priorities",
                    "label": "Refine Priorities",
                    "description": "Adjust priority rankings",
                }
            )

        elif current_step == 5:
            # Roadmap step
            actions.append(
                {
                    "action": "export_roadmap",
                    "label": "Export Roadmap",
                    "description": "Download the implementation roadmap",
                }
            )
            actions.append(
                {
                    "action": "share_roadmap",
                    "label": "Share Roadmap",
                    "description": "Share with team members",
                }
            )

        return actions
