# discovery/app/agents/analysis_agent.py
"""Analysis subagent for Step 4: Analysis & Scoring."""
from typing import Any, Optional

from app.agents.base import BaseSubagent
from app.services.analysis_service import AnalysisService
from app.schemas.analysis import AnalysisDimension


class AnalysisSubagent(BaseSubagent):
    """Handles analysis and scoring operations."""

    agent_type: str = "analysis"

    def __init__(
        self,
        session: Any,
        analysis_service: AnalysisService,
        memory_service: Any = None,
    ) -> None:
        super().__init__(session, memory_service)
        self.analysis_service = analysis_service
        self._analysis_complete = False

    async def process(self, message: str) -> dict[str, Any]:
        """Process user message for analysis step."""
        message_lower = message.lower()

        # Check if analysis has been run
        summary = await self.analysis_service.get_all_dimensions(self.session.id)

        # Handle calculate/run analysis
        if any(word in message_lower for word in ["calculate", "run", "analyze", "score"]):
            result = await self.analysis_service.trigger_analysis(self.session.id)
            if result and result.get("status") == "completed":
                self._analysis_complete = True
                count = result.get("count", 0)
                return {
                    "message": f"Analysis complete! Scored {count} roles. Explore results by dimension.",
                    "quick_actions": ["View by role", "View by department", "Continue to roadmap"],
                    "step_complete": False,
                }
            return {
                "message": "Analysis failed. Please ensure you have confirmed role mappings.",
                "quick_actions": ["Go back to mappings", "Retry analysis"],
                "step_complete": False,
            }

        # Handle continue/done
        if any(word in message_lower for word in ["continue", "done", "next", "roadmap"]):
            if summary or self._analysis_complete:
                return {
                    "message": "Analysis complete. Moving to roadmap generation.",
                    "quick_actions": [],
                    "step_complete": True,
                }
            return {
                "message": "Please run the analysis first before continuing.",
                "quick_actions": ["Run analysis"],
                "step_complete": False,
            }

        # Handle dimension views
        dimension_map = {
            "role": AnalysisDimension.ROLE,
            "department": AnalysisDimension.DEPARTMENT,
            "geography": AnalysisDimension.GEOGRAPHY,
            "geo": AnalysisDimension.GEOGRAPHY,
            "task": AnalysisDimension.TASK,
        }

        for key, dimension in dimension_map.items():
            if key in message_lower:
                results = await self.analysis_service.get_by_dimension(
                    self.session.id, dimension
                )
                if results and results.get("results"):
                    items = results["results"][:5]
                    lines = []
                    for item in items:
                        score = int(item.get("ai_exposure_score", 0) * 100)
                        tier = item.get("priority_tier", "?")
                        lines.append(f"- {item['name']}: {score}% exposure ({tier})")
                    summary_text = "\n".join(lines)
                    if len(results["results"]) > 5:
                        summary_text += f"\n... and {len(results['results']) - 5} more"
                    return {
                        "message": f"Analysis by {dimension.value}:\n\n{summary_text}",
                        "quick_actions": ["View by role", "View by department", "Continue to roadmap"],
                        "step_complete": False,
                    }
                return {
                    "message": f"No results found for {dimension.value}. Run analysis first.",
                    "quick_actions": ["Run analysis"],
                    "step_complete": False,
                }

        # Default: Check if analysis exists
        if summary:
            self._analysis_complete = True
            dim_summary = []
            for dim, data in summary.items():
                count = data.get("count", 0)
                avg = int(data.get("avg_exposure", 0) * 100)
                dim_summary.append(f"- {dim}: {count} items, {avg}% avg exposure")
            summary_text = "\n".join(dim_summary)
            return {
                "message": f"Analysis Summary:\n\n{summary_text}",
                "quick_actions": ["View by role", "View by department", "Continue to roadmap"],
                "step_complete": False,
            }

        # No analysis yet
        return {
            "message": "Ready to run analysis. This will calculate AI exposure and priority scores for all mapped roles.",
            "quick_actions": ["Run analysis"],
            "step_complete": False,
        }
