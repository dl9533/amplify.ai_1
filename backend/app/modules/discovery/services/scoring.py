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
