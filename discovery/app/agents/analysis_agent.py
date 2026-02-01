"""Analysis Subagent for score calculation and insight generation."""
from typing import Any, Optional

from app.agents.base import BaseSubagent


class AnalysisSubagent(BaseSubagent):
    """Subagent for score calculation orchestration and insight generation.

    This agent handles the analysis phase of the discovery process,
    delegating score calculations to the ScoringService and generating
    insights based on the results.

    Attributes:
        agent_type: The type identifier for this agent ('analysis').
        _scoring_service: Service for score calculations.
        _scoring_result: The result from the most recent scoring run.
        _scores_calculated: Whether scores have been calculated.
    """

    agent_type: str = "analysis"

    def __init__(self, session: Any, memory_service: Any) -> None:
        """Initialize the AnalysisSubagent.

        Args:
            session: Database session for persistence operations.
            memory_service: Service for agent memory management.
        """
        super().__init__(session, memory_service)
        self._scoring_service: Optional[Any] = None
        self._scoring_result: Optional[Any] = None
        self._scores_calculated: bool = False

    async def calculate_scores(self) -> Any:
        """Calculate scores by delegating to the ScoringService.

        Returns:
            The scoring result from ScoringService.

        Raises:
            ValueError: If no scoring service is configured.
        """
        if self._scoring_service is None:
            raise ValueError("No scoring service configured")

        result = await self._scoring_service.score_session()
        self._scoring_result = result
        self._scores_calculated = True
        return result

    async def generate_insights(self) -> list[str]:
        """Generate insights based on scoring results.

        Returns:
            A list of insight strings describing key findings.
        """
        insights: list[str] = []

        if self._scoring_result is None:
            return insights

        # Generate insights about top opportunities based on priority scores
        role_scores = getattr(self._scoring_result, "role_scores", {})
        if role_scores:
            # Sort roles by priority
            sorted_roles = sorted(
                role_scores.items(),
                key=lambda x: getattr(x[1], "priority", 0),
                reverse=True,
            )
            if sorted_roles:
                top_role, top_score = sorted_roles[0]
                priority = getattr(top_score, "priority", 0)
                insights.append(
                    f"Top automation opportunity: {top_role} with priority score {priority:.2f}"
                )

        return insights

    async def get_dimension_summary(self, dimension: str) -> list[Any]:
        """Get a summary of scores filtered by dimension.

        Args:
            dimension: The dimension to filter by (e.g., 'DEPARTMENT').

        Returns:
            A list of aggregations for the specified dimension.
        """
        if self._scoring_result is None:
            return []

        aggregations = getattr(self._scoring_result, "dimension_aggregations", [])
        return [
            agg for agg in aggregations
            if getattr(agg, "dimension", None) == dimension
        ]

    async def process(self, message: str) -> dict[str, Any]:
        """Process an incoming message and return a response.

        Implements a brainstorming-style interaction where the agent
        presents analysis dimensions for exploration.

        Args:
            message: The input message to process.

        Returns:
            A structured response dictionary with message and choices.
        """
        if self._scores_calculated:
            return self.format_response(
                message="Analysis complete. Which dimension would you like to explore?",
                question="Select an analysis dimension:",
                choices=[
                    "By Role",
                    "By Department",
                    "By Geography",
                    "By Task",
                ],
            )

        return self.format_response(
            message="Ready to analyze discovery session data.",
            question="Would you like to calculate scores?",
            choices=["Calculate scores"],
        )
