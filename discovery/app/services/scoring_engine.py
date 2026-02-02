# discovery/app/services/scoring_engine.py
"""Scoring engine for AI exposure and priority calculations."""
from dataclasses import dataclass


@dataclass
class RoleScores:
    """Scores for a role."""
    ai_exposure: float
    impact: float
    complexity: float
    priority: float


class ScoringEngine:
    """Engine for calculating discovery scores.

    Scoring formulas based on design spec:
    - AI Exposure: Average of selected DWA exposure scores
    - Impact: Exposure × (row_count / total_rows) normalized
    - Complexity: 1 - Exposure (harder to automate = lower exposure)
    - Priority: (Exposure×0.4) + (Impact×0.4) + ((1-Complexity)×0.2)
    """

    # Weight factors for priority calculation
    EXPOSURE_WEIGHT = 0.4
    IMPACT_WEIGHT = 0.4
    EASE_WEIGHT = 0.2  # (1 - complexity)

    def calculate_ai_exposure(self, dwa_scores: list[float]) -> float:
        """Calculate AI exposure from DWA scores.

        Args:
            dwa_scores: List of exposure scores (0.0-1.0) for selected DWAs.

        Returns:
            Average exposure score.
        """
        if not dwa_scores:
            return 0.0
        return sum(dwa_scores) / len(dwa_scores)

    def calculate_impact(
        self,
        exposure: float,
        row_count: int,
        total_rows: int,
    ) -> float:
        """Calculate impact score.

        Impact considers both AI exposure and workforce coverage.

        Args:
            exposure: AI exposure score (0.0-1.0).
            row_count: Number of employees in this role.
            total_rows: Total employees in dataset.

        Returns:
            Impact score (0.0-1.0).
        """
        if total_rows == 0:
            return 0.0

        coverage = row_count / total_rows
        # Weighted combination of exposure and coverage
        return min(1.0, exposure * 0.6 + coverage * 0.4)

    def calculate_complexity(self, exposure: float) -> float:
        """Calculate complexity score.

        Complexity is the inverse of exposure - lower exposure means
        the work is harder to automate.

        Args:
            exposure: AI exposure score (0.0-1.0).

        Returns:
            Complexity score (0.0-1.0).
        """
        return 1.0 - exposure

    def calculate_priority(
        self,
        exposure: float,
        impact: float,
        complexity: float,
    ) -> float:
        """Calculate priority score.

        Priority favors high exposure, high impact, low complexity.

        Args:
            exposure: AI exposure score.
            impact: Impact score.
            complexity: Complexity score.

        Returns:
            Priority score (0.0-1.0).
        """
        ease = 1.0 - complexity
        return (
            exposure * self.EXPOSURE_WEIGHT
            + impact * self.IMPACT_WEIGHT
            + ease * self.EASE_WEIGHT
        )

    def score_role(
        self,
        dwa_scores: list[float],
        row_count: int,
        total_rows: int,
    ) -> dict[str, float]:
        """Calculate all scores for a role.

        Args:
            dwa_scores: Exposure scores for selected DWAs.
            row_count: Employees in this role.
            total_rows: Total employees.

        Returns:
            Dict with ai_exposure, impact, complexity, priority.
        """
        exposure = self.calculate_ai_exposure(dwa_scores)
        impact = self.calculate_impact(exposure, row_count, total_rows)
        complexity = self.calculate_complexity(exposure)
        priority = self.calculate_priority(exposure, impact, complexity)

        return {
            "ai_exposure": round(exposure, 3),
            "impact": round(impact, 3),
            "complexity": round(complexity, 3),
            "priority": round(priority, 3),
        }

    def classify_priority_tier(self, priority: float, complexity: float) -> str:
        """Classify into priority tier.

        Args:
            priority: Priority score.
            complexity: Complexity score.

        Returns:
            'now', 'next_quarter', or 'future'.
        """
        if priority >= 0.75 and complexity < 0.3:
            return "now"
        elif priority >= 0.60:
            return "next_quarter"
        else:
            return "future"
