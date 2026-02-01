"""Roadmap Subagent for candidate prioritization and timeline generation."""
from typing import Any

from app.agents.base import BaseSubagent


class RoadmapSubagent(BaseSubagent):
    """Subagent for candidate prioritization and implementation timeline generation.

    This agent handles the roadmap phase of the discovery process,
    prioritizing automation candidates and organizing them into
    quarterly implementation timelines.

    Attributes:
        agent_type: The type identifier for this agent ('roadmap').
        _candidates: List of candidates to prioritize.
        _prioritized: Whether prioritization has been completed.
    """

    agent_type: str = "roadmap"

    # Tier thresholds
    HIGH_TIER_THRESHOLD: float = 0.7
    MEDIUM_TIER_THRESHOLD: float = 0.4

    def __init__(self, session: Any, memory_service: Any) -> None:
        """Initialize the RoadmapSubagent.

        Args:
            session: Database session for persistence operations.
            memory_service: Service for agent memory management.
        """
        super().__init__(session, memory_service)
        self._candidates: list[Any] = []
        self._prioritized: bool = False

    async def prioritize(self, candidates: list[Any]) -> list[Any]:
        """Prioritize candidates by their priority score in descending order.

        Args:
            candidates: List of candidate objects with priority_score attribute.

        Returns:
            List of candidates sorted by priority_score descending.
        """
        return sorted(
            candidates,
            key=lambda c: getattr(c, "priority_score", 0),
            reverse=True,
        )

    async def assign_tiers(self, candidates: list[Any]) -> dict[str, str]:
        """Assign priority tiers to candidates based on their scores.

        Tier thresholds:
        - High: priority_score >= 0.7
        - Medium: priority_score >= 0.4
        - Low: priority_score < 0.4

        Args:
            candidates: List of candidate objects with id and priority_score.

        Returns:
            Dictionary mapping candidate id to tier ("high", "medium", "low").
        """
        tiers: dict[str, str] = {}

        for candidate in candidates:
            candidate_id = getattr(candidate, "id", str(id(candidate)))
            score = getattr(candidate, "priority_score", 0)

            if score >= self.HIGH_TIER_THRESHOLD:
                tiers[candidate_id] = "high"
            elif score >= self.MEDIUM_TIER_THRESHOLD:
                tiers[candidate_id] = "medium"
            else:
                tiers[candidate_id] = "low"

        return tiers

    async def generate_timeline(
        self,
        candidates: list[Any],
        quarters: int = 4,
    ) -> dict[str, list[Any]]:
        """Generate a quarterly implementation timeline for candidates.

        Candidates are assigned to quarters based on a combination of
        priority score and complexity. High priority, low complexity
        items are scheduled earlier.

        Args:
            candidates: List of candidate objects with priority_score and complexity_score.
            quarters: Number of quarters to plan (default: 4).

        Returns:
            Dictionary mapping quarter labels (Q1, Q2, etc.) to lists of candidates.
        """
        # Initialize timeline with empty quarters
        timeline: dict[str, list[Any]] = {
            f"Q{i+1}": [] for i in range(quarters)
        }

        if not candidates:
            return timeline

        # Calculate implementation score: high priority + low complexity = earlier
        # Score = priority - complexity (higher score = schedule sooner)
        def impl_score(c: Any) -> float:
            priority = getattr(c, "priority_score", 0)
            complexity = getattr(c, "complexity_score", 0.5)
            return priority - complexity

        # Sort candidates by implementation score (descending)
        sorted_candidates = sorted(candidates, key=impl_score, reverse=True)

        # Distribute candidates across quarters
        candidates_per_quarter = max(1, len(sorted_candidates) // quarters)

        for i, candidate in enumerate(sorted_candidates):
            quarter_index = min(i // candidates_per_quarter, quarters - 1)
            timeline[f"Q{quarter_index + 1}"].append(candidate)

        return timeline

    async def process(self, message: str) -> dict[str, Any]:
        """Process an incoming message and return a response.

        Implements a brainstorming-style interaction where the agent
        guides users through prioritization and timeline generation.

        Args:
            message: The input message to process.

        Returns:
            A structured response dictionary with message, question, and choices.
        """
        if self._prioritized:
            return self.format_response(
                message="Candidates prioritized. Ready to generate implementation timeline.",
                question="Select timeline duration:",
                choices=[
                    "1 Quarter",
                    "2 Quarters",
                    "4 Quarters (1 Year)",
                    "8 Quarters (2 Years)",
                ],
            )

        if self._candidates:
            return self.format_response(
                message="Ready to prioritize automation candidates.",
                question="How would you like to prioritize?",
                choices=[
                    "By priority score",
                    "By ROI potential",
                    "By implementation complexity",
                    "Custom criteria",
                ],
            )

        return self.format_response(
            message="Roadmap planning agent ready. Load candidates to begin prioritization.",
            question="Would you like to load candidates from the analysis phase?",
            choices=[
                "Load candidates",
                "Import from file",
            ],
        )
