"""Scoring service for discovery opportunity analysis.

Provides the ScoringService for calculating impact scores based on
role headcount and AI exposure scores. Impact scores help prioritize
which roles have the highest potential for AI agent automation.
"""

from typing import Any


class ScoringService:
    """Service for calculating impact and priority scores.

    This service calculates impact scores for role mappings based on:
    - Role headcount (row_count): Number of employees in a role
    - AI exposure score: How automatable the role's tasks are (0.0-1.0)

    Impact is calculated as: (role_count * exposure) / max_headcount
    This normalizes the score to a 0-1 range for consistent comparison.

    Attributes:
        DEFAULT_MAX_HEADCOUNT: Default maximum headcount for normalization (1000).
    """

    DEFAULT_MAX_HEADCOUNT = 1000

    def calculate_impact_score(
        self,
        role_mapping: Any,
        exposure_score: float,
        max_headcount: int = DEFAULT_MAX_HEADCOUNT,
    ) -> float:
        """Calculate the impact score for a single role mapping.

        Impact is calculated as (role_count * exposure_score) / max_headcount,
        capped at 1.0 to ensure the result is always in the 0-1 range.

        Args:
            role_mapping: A role mapping object with a row_count attribute
                representing the number of employees in this role.
            exposure_score: AI exposure score for the role (0.0-1.0).
            max_headcount: Maximum headcount for normalization. Defaults to 1000.
                Higher values mean individual roles contribute less to the score.

        Returns:
            Impact score normalized to 0.0-1.0 range. Returns 0.0 if either
            row_count is 0 or exposure_score is 0.0.

        Example:
            >>> service = ScoringService()
            >>> role = MagicMock(row_count=100)
            >>> service.calculate_impact_score(role, exposure_score=0.8)
            0.08
        """
        row_count = role_mapping.row_count or 0

        # Early return for zero values
        if row_count == 0 or exposure_score == 0.0:
            return 0.0

        # Calculate raw impact and normalize
        raw_impact = row_count * exposure_score
        normalized_impact = raw_impact / max_headcount

        # Cap at 1.0 to ensure result is always in 0-1 range
        return min(normalized_impact, 1.0)

    def calculate_impact_scores_for_session(
        self,
        role_mappings: list[Any],
        exposure_scores: dict[str, float],
    ) -> dict[str, float]:
        """Calculate impact scores for all role mappings in a session.

        Uses the maximum row_count from the provided role mappings as the
        normalization factor, ensuring scores are relative to the session's
        largest role.

        Args:
            role_mappings: List of role mapping objects, each with id and
                row_count attributes.
            exposure_scores: Dictionary mapping role_mapping.id to exposure
                score (0.0-1.0).

        Returns:
            Dictionary mapping role_mapping.id to calculated impact score.
            Roles without a matching exposure score are skipped.

        Example:
            >>> service = ScoringService()
            >>> mappings = [MagicMock(id="role-1", row_count=100)]
            >>> exposures = {"role-1": 0.8}
            >>> service.calculate_impact_scores_for_session(mappings, exposures)
            {"role-1": 0.8}
        """
        if not role_mappings:
            return {}

        # Find max headcount for normalization
        max_headcount = max(
            (rm.row_count or 0 for rm in role_mappings),
            default=self.DEFAULT_MAX_HEADCOUNT,
        )

        # Use default if max is 0 to avoid division issues
        if max_headcount == 0:
            max_headcount = self.DEFAULT_MAX_HEADCOUNT

        impacts: dict[str, float] = {}
        for role_mapping in role_mappings:
            role_id = role_mapping.id
            if role_id in exposure_scores:
                exposure = exposure_scores[role_id]
                impacts[role_id] = self.calculate_impact_score(
                    role_mapping=role_mapping,
                    exposure_score=exposure,
                    max_headcount=max_headcount,
                )

        return impacts

    def calculate_priority_score(
        self,
        exposure: float,
        impact: float,
        complexity: float,
        weights: dict[str, float] | None = None,
    ) -> float:
        """Calculate the priority score for a role based on weighted factors.

        Priority is calculated using a weighted formula that considers exposure,
        impact, and inverse complexity. Higher priority means the role should
        be addressed sooner for AI automation opportunities.

        Formula: (exposure * w_e) + (impact * w_i) + ((1 - complexity) * w_c)

        The inverse of complexity is used because lower complexity makes a role
        easier to automate, thus higher priority.

        Args:
            exposure: AI exposure score for the role (0.0-1.0). Higher means
                more tasks can be automated by AI.
            impact: Impact score for the role (0.0-1.0). Higher means more
                business value from automation.
            complexity: Complexity score for the role (0.0-1.0). Higher means
                the role is harder to automate.
            weights: Optional custom weights dictionary with keys 'exposure',
                'impact', and 'complexity'. Values should sum to 1.0.
                Defaults to exposure=0.4, impact=0.4, complexity=0.2.

        Returns:
            Priority score normalized to 0.0-1.0 range.

        Example:
            >>> service = ScoringService()
            >>> service.calculate_priority_score(0.8, 0.6, 0.3)
            0.70
        """
        # Default weights: exposure=40%, impact=40%, inverse_complexity=20%
        default_weights = {"exposure": 0.4, "impact": 0.4, "complexity": 0.2}
        w = weights if weights is not None else default_weights

        # Calculate weighted priority
        # Note: complexity contribution is inverted (1 - complexity)
        priority = (
            (exposure * w["exposure"])
            + (impact * w["impact"])
            + ((1 - complexity) * w["complexity"])
        )

        # Ensure result is bounded to 0-1 range
        return max(0.0, min(1.0, priority))

    def calculate_complexity_score(self, exposure: float) -> float:
        """Calculate complexity score as the inverse of exposure.

        This provides a simple approximation where tasks with high AI exposure
        (easily automated) have low complexity, and tasks with low AI exposure
        (hard to automate) have high complexity.

        Args:
            exposure: AI exposure score (0.0-1.0).

        Returns:
            Complexity score (0.0-1.0), calculated as 1 - exposure.

        Example:
            >>> service = ScoringService()
            >>> service.calculate_complexity_score(0.75)
            0.25
        """
        return 1.0 - exposure

    def calculate_all_scores_for_role(
        self,
        role_mapping: Any,
        selected_dwas: list[Any],
        max_headcount: int = DEFAULT_MAX_HEADCOUNT,
    ) -> dict[str, float]:
        """Calculate all scores (exposure, impact, complexity, priority) for a role.

        This method aggregates exposure from selected DWAs (Detailed Work Activities),
        derives complexity from exposure, calculates impact from role headcount
        and exposure, and finally computes the overall priority score.

        Args:
            role_mapping: A role mapping object with id and row_count attributes.
            selected_dwas: List of DWA objects with ai_exposure_override attribute.
                The average of these values becomes the role's exposure score.
            max_headcount: Maximum headcount for impact normalization.
                Defaults to 1000.

        Returns:
            Dictionary with keys 'exposure', 'impact', 'complexity', 'priority',
            each containing a float score in the 0.0-1.0 range.

        Example:
            >>> service = ScoringService()
            >>> role = MagicMock(id="role-1", row_count=200)
            >>> dwas = [MagicMock(ai_exposure_override=0.8)]
            >>> service.calculate_all_scores_for_role(role, dwas, 1000)
            {'exposure': 0.8, 'impact': 0.16, 'complexity': 0.2, 'priority': ...}
        """
        # Calculate exposure as average of DWA exposures
        if selected_dwas:
            total_exposure = sum(dwa.ai_exposure_override for dwa in selected_dwas)
            exposure = total_exposure / len(selected_dwas)
        else:
            exposure = 0.0

        # Derive complexity from exposure (inverse relationship)
        complexity = self.calculate_complexity_score(exposure)

        # Calculate impact using existing method
        impact = self.calculate_impact_score(
            role_mapping=role_mapping,
            exposure_score=exposure,
            max_headcount=max_headcount,
        )

        # Calculate priority from all three scores
        priority = self.calculate_priority_score(
            exposure=exposure,
            impact=impact,
            complexity=complexity,
        )

        return {
            "exposure": exposure,
            "impact": impact,
            "complexity": complexity,
            "priority": priority,
        }
