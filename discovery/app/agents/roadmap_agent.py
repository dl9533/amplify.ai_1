# discovery/app/agents/roadmap_agent.py
"""Roadmap subagent for Step 5: Candidate Generation & Prioritization."""
from typing import Any, Optional
from uuid import UUID

from app.agents.base import BaseSubagent
from app.services.roadmap_service import RoadmapService


class RoadmapSubagent(BaseSubagent):
    """Handles candidate generation and prioritization."""

    agent_type: str = "roadmap"

    def __init__(
        self,
        session: Any,
        roadmap_service: RoadmapService,
        memory_service: Any = None,
    ) -> None:
        super().__init__(session, memory_service)
        self.roadmap_service = roadmap_service
        self._candidates_generated = False
        self._pending_selection: Optional[str] = None

    async def process(self, message: str) -> dict[str, Any]:
        """Process user message for roadmap step."""
        message_lower = message.lower()

        # Get current candidates
        candidates = await self.roadmap_service.get_candidates(self.session.id)

        # Handle generate candidates
        if any(word in message_lower for word in ["generate", "create", "build candidates"]):
            result = await self.roadmap_service.generate_candidates(self.session.id)
            self._candidates_generated = True
            count = len(result) if result else 0
            return {
                "message": f"Generated {count} agentification candidates from analysis results.",
                "quick_actions": ["View candidates", "Filter by tier", "Select for build"],
                "step_complete": False,
            }

        # Handle selection confirmation
        if self._pending_selection:
            if any(word in message_lower for word in ["yes", "select", "confirm"]):
                await self.roadmap_service.select_for_build(
                    UUID(self._pending_selection), True
                )
                self._pending_selection = None
                return {
                    "message": "Candidate selected for build pipeline.",
                    "quick_actions": ["Select more", "View all selected", "Finish and handoff"],
                    "step_complete": False,
                }
            elif any(word in message_lower for word in ["no", "skip", "cancel"]):
                self._pending_selection = None
                return {
                    "message": "Selection cancelled.",
                    "quick_actions": ["View candidates", "Finish and handoff"],
                    "step_complete": False,
                }

        # Handle finish/complete
        if any(word in message_lower for word in ["finish", "complete", "done", "handoff"]):
            selected = [c for c in candidates if c.get("selected_for_build")]
            if not selected:
                return {
                    "message": "No candidates selected for build. Select at least one to proceed.",
                    "quick_actions": ["View candidates", "Select all 'Now' tier"],
                    "step_complete": False,
                }
            return {
                "message": f"Discovery complete! {len(selected)} candidates ready for Build pipeline handoff.",
                "quick_actions": [],
                "step_complete": True,
            }

        # Handle tier filter
        for tier in ["now", "next_quarter", "next", "future", "later"]:
            if tier in message_lower:
                tier_key = "next_quarter" if tier == "next" else ("future" if tier == "later" else tier)
                filtered = await self.roadmap_service.get_candidates(self.session.id, tier_key)
                if filtered:
                    lines = []
                    for c in filtered[:5]:
                        impact = int(c.get("estimated_impact", 0) * 100)
                        selected = "+" if c.get("selected_for_build") else "o"
                        lines.append(f"{selected} {c['name']} ({impact}% impact)")
                    summary = "\n".join(lines)
                    if len(filtered) > 5:
                        summary += f"\n... and {len(filtered) - 5} more"
                    return {
                        "message": f"{tier_key.replace('_', ' ').title()} tier candidates:\n\n{summary}",
                        "quick_actions": ["Select all in tier", "View all", "Finish"],
                        "step_complete": False,
                    }
                return {
                    "message": f"No candidates in {tier_key} tier.",
                    "quick_actions": ["View all", "Generate candidates"],
                    "step_complete": False,
                }

        # Default: Show candidate summary
        if not candidates:
            return {
                "message": "No candidates generated yet. Generate candidates from analysis results to begin.",
                "quick_actions": ["Generate candidates"],
                "step_complete": False,
            }

        now_count = sum(1 for c in candidates if c.get("priority_tier") == "now")
        next_count = sum(1 for c in candidates if c.get("priority_tier") == "next_quarter")
        future_count = sum(1 for c in candidates if c.get("priority_tier") == "future")
        selected_count = sum(1 for c in candidates if c.get("selected_for_build"))

        # Show a few top candidates
        lines = []
        for c in candidates[:5]:
            tier = c.get("priority_tier", "?")
            impact = int(c.get("estimated_impact", 0) * 100)
            selected = "+" if c.get("selected_for_build") else "o"
            lines.append(f"{selected} {c['name']} - {tier} ({impact}%)")

        summary = "\n".join(lines)
        if len(candidates) > 5:
            summary += f"\n... and {len(candidates) - 5} more"

        return {
            "message": f"Agentification Candidates ({selected_count} selected for build):\n\n"
                      f"Now: {now_count} | Next Quarter: {next_count} | Future: {future_count}\n\n{summary}",
            "quick_actions": [
                "Filter by 'Now' tier",
                "Select for build",
                "Finish and handoff",
            ],
            "step_complete": False,
        }
