# discovery/app/agents/mapping_agent.py
"""Mapping subagent for Step 2: Role Mapping."""
from typing import Any, Optional

from app.agents.base import BaseSubagent
from app.services.role_mapping_service import RoleMappingService


class MappingSubagent(BaseSubagent):
    """Handles role-to-O*NET occupation mapping."""

    agent_type: str = "mapping"

    def __init__(
        self,
        session: Any,
        mapping_service: RoleMappingService,
        memory_service: Any = None,
    ) -> None:
        super().__init__(session, memory_service)
        self.mapping_service = mapping_service

    async def process(self, message: str) -> dict[str, Any]:
        """Process user message for mapping step."""
        message_lower = message.lower()

        # Get current mappings
        mappings = await self.mapping_service.get_by_session_id(self.session.id)

        if not mappings:
            return {
                "message": "No role mappings found. Please complete the upload step first.",
                "quick_actions": ["Go back to upload"],
                "step_complete": False,
            }

        # Handle bulk confirm
        if any(word in message_lower for word in ["accept all", "confirm all", "bulk"]):
            result = await self.mapping_service.bulk_confirm(
                self.session.id,
                min_confidence=0.85,
            )
            confirmed = result.get("confirmed_count", 0)
            return {
                "message": f"Confirmed {confirmed} high-confidence mappings (>85%).",
                "quick_actions": ["Show remaining", "Continue to activities"],
                "step_complete": False,
            }

        # Handle continue/done
        if any(word in message_lower for word in ["continue", "done", "next", "proceed"]):
            unconfirmed = [m for m in mappings if not m.get("user_confirmed")]
            if unconfirmed:
                return {
                    "message": f"You have {len(unconfirmed)} unconfirmed mappings. Continue anyway?",
                    "quick_actions": ["Yes, continue", "Review unconfirmed"],
                    "step_complete": False,
                }
            return {
                "message": "All mappings confirmed. Moving to activity selection.",
                "quick_actions": [],
                "step_complete": True,
            }

        # Handle search
        if "search" in message_lower:
            query = message_lower.replace("search", "").strip()
            if query and hasattr(self.mapping_service, "search_occupations"):
                results = await self.mapping_service.search_occupations(query)
                if results:
                    titles = [f"- {r.get('title', '')} ({r.get('code', '')})" for r in results[:5]]
                    return {
                        "message": f"Found these O*NET occupations:\n" + "\n".join(titles),
                        "quick_actions": [r.get("code", "") for r in results[:3]],
                        "step_complete": False,
                    }

        # Default: Show mapping summary
        confirmed = sum(1 for m in mappings if m.get("user_confirmed"))
        high_conf = sum(1 for m in mappings if m.get("confidence_score", 0) >= 0.85)

        mapping_lines = []
        for m in mappings[:10]:
            status = "+" if m.get("user_confirmed") else "o"
            conf = int(m.get("confidence_score", 0) * 100)
            mapping_lines.append(
                f"{status} {m['source_role']} -> {m.get('onet_code', '?')} ({conf}%)"
            )

        summary = "\n".join(mapping_lines)
        if len(mappings) > 10:
            summary += f"\n... and {len(mappings) - 10} more"

        return {
            "message": f"Role Mappings ({confirmed}/{len(mappings)} confirmed):\n\n{summary}",
            "quick_actions": [
                "Accept all >85%",
                "Search occupation",
                "Continue to activities",
            ],
            "step_complete": False,
        }
