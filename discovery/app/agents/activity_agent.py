# discovery/app/agents/activity_agent.py
"""Activity subagent for Step 3: Activity Selection."""
from typing import Any, Optional

from app.agents.base import BaseSubagent
from app.services.activity_service import ActivityService


class ActivitySubagent(BaseSubagent):
    """Handles DWA (Detailed Work Activity) selection."""

    agent_type: str = "activity"

    def __init__(
        self,
        session: Any,
        activity_service: ActivityService,
        memory_service: Any = None,
    ) -> None:
        super().__init__(session, memory_service)
        self.activity_service = activity_service
        self._current_role_mapping_id: Optional[str] = None

    async def process(self, message: str) -> dict[str, Any]:
        """Process user message for activity selection step."""
        message_lower = message.lower()

        # Get current selections
        selections = await self.activity_service.get_selections(self.session.id)

        # Handle bulk select
        if any(word in message_lower for word in ["select all", "bulk", "auto"]):
            result = await self.activity_service.bulk_select(
                self.session.id,
                select_all=True,
            )
            selected = result.get("selected_count", 0)
            return {
                "message": f"Auto-selected {selected} high-exposure activities (>60% AI exposure).",
                "quick_actions": ["Review selections", "Continue to analysis"],
                "step_complete": False,
            }

        # Handle continue/done
        if any(word in message_lower for word in ["continue", "done", "next", "analysis"]):
            selected_count = sum(1 for s in selections if s.get("selected"))
            if selected_count == 0 and selections:
                return {
                    "message": "No activities selected. Would you like to auto-select high-exposure activities?",
                    "quick_actions": ["Auto-select", "Skip activities"],
                    "step_complete": False,
                }
            return {
                "message": f"Activity selection complete ({selected_count} selected). Moving to analysis.",
                "quick_actions": [],
                "step_complete": True,
            }

        # Handle deselect all
        if "deselect" in message_lower or "clear" in message_lower:
            result = await self.activity_service.bulk_select(
                self.session.id,
                select_all=False,
            )
            return {
                "message": "All activities deselected.",
                "quick_actions": ["Auto-select", "Continue to analysis"],
                "step_complete": False,
            }

        # Default: Show activity summary
        if not selections:
            return {
                "message": "No activities loaded yet. Activities will be loaded from O*NET based on your role mappings.",
                "quick_actions": ["Load activities", "Go back to mappings"],
                "step_complete": False,
            }

        selected_count = sum(1 for s in selections if s.get("selected"))
        total_count = len(selections)

        # Show a few example activities
        activity_lines = []
        for s in selections[:8]:
            status = "+" if s.get("selected") else "o"
            name = s.get("dwa_name", s.get("dwa_id", "?"))
            activity_lines.append(f"{status} {name}")

        summary = "\n".join(activity_lines)
        if len(selections) > 8:
            summary += f"\n... and {len(selections) - 8} more"

        return {
            "message": f"Activity Selections ({selected_count}/{total_count} selected):\n\n{summary}",
            "quick_actions": [
                "Auto-select high-exposure",
                "Select all",
                "Continue to analysis",
            ],
            "step_complete": False,
        }
