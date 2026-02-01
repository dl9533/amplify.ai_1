# backend/tests/unit/modules/discovery/test_priority_scoring.py
import pytest
from unittest.mock import MagicMock

from app.modules.discovery.services.scoring import ScoringService


@pytest.fixture
def scoring_service():
    return ScoringService()


class TestPriorityScoreCalculator:
    """Tests for priority score: priority = (exposure * 0.4) + (impact * 0.4) + ((1 - complexity) * 0.2)."""

    def test_priority_score_formula(self, scoring_service):
        """Priority should follow weighted formula."""
        exposure = 0.8
        impact = 0.6
        complexity = 0.3

        priority = scoring_service.calculate_priority_score(
            exposure=exposure,
            impact=impact,
            complexity=complexity
        )

        # (0.8 * 0.4) + (0.6 * 0.4) + ((1 - 0.3) * 0.2)
        # = 0.32 + 0.24 + 0.14
        # = 0.70
        assert priority == pytest.approx(0.70, rel=0.01)

    def test_priority_high_exposure_high_impact_low_complexity(self, scoring_service):
        """Best case: high exposure, high impact, low complexity should give max priority."""
        priority = scoring_service.calculate_priority_score(
            exposure=1.0,
            impact=1.0,
            complexity=0.0
        )

        # (1.0 * 0.4) + (1.0 * 0.4) + ((1 - 0.0) * 0.2) = 0.4 + 0.4 + 0.2 = 1.0
        assert priority == pytest.approx(1.0, rel=0.01)

    def test_priority_low_exposure_low_impact_high_complexity(self, scoring_service):
        """Worst case: low exposure, low impact, high complexity should give min priority."""
        priority = scoring_service.calculate_priority_score(
            exposure=0.0,
            impact=0.0,
            complexity=1.0
        )

        # (0.0 * 0.4) + (0.0 * 0.4) + ((1 - 1.0) * 0.2) = 0 + 0 + 0 = 0.0
        assert priority == pytest.approx(0.0, rel=0.01)

    def test_priority_exposure_weight_is_40_percent(self, scoring_service):
        """Exposure should contribute 40% to priority."""
        priority = scoring_service.calculate_priority_score(
            exposure=1.0,
            impact=0.0,
            complexity=1.0  # complexity=1 means (1-1)*0.2 = 0
        )

        assert priority == pytest.approx(0.4, rel=0.01)

    def test_priority_impact_weight_is_40_percent(self, scoring_service):
        """Impact should contribute 40% to priority."""
        priority = scoring_service.calculate_priority_score(
            exposure=0.0,
            impact=1.0,
            complexity=1.0
        )

        assert priority == pytest.approx(0.4, rel=0.01)

    def test_priority_inverse_complexity_weight_is_20_percent(self, scoring_service):
        """Inverse complexity should contribute 20% to priority."""
        priority = scoring_service.calculate_priority_score(
            exposure=0.0,
            impact=0.0,
            complexity=0.0  # (1 - 0) * 0.2 = 0.2
        )

        assert priority == pytest.approx(0.2, rel=0.01)

    def test_priority_bounded_zero_to_one(self, scoring_service):
        """Priority score should always be between 0 and 1."""
        test_cases = [
            (0.0, 0.0, 0.0),
            (1.0, 1.0, 1.0),
            (0.5, 0.5, 0.5),
            (0.9, 0.1, 0.3),
            (0.2, 0.8, 0.7),
        ]

        for exposure, impact, complexity in test_cases:
            priority = scoring_service.calculate_priority_score(
                exposure=exposure,
                impact=impact,
                complexity=complexity
            )
            assert 0.0 <= priority <= 1.0, f"Failed for ({exposure}, {impact}, {complexity})"

    def test_priority_with_custom_weights(self, scoring_service):
        """Should allow custom weights for different prioritization strategies."""
        priority = scoring_service.calculate_priority_score(
            exposure=1.0,
            impact=0.0,
            complexity=1.0,
            weights={"exposure": 0.6, "impact": 0.3, "complexity": 0.1}
        )

        # 1.0 * 0.6 + 0.0 * 0.3 + (1 - 1.0) * 0.1 = 0.6
        assert priority == pytest.approx(0.6, rel=0.01)

    def test_calculate_complexity_from_exposure(self, scoring_service):
        """Complexity should be inverse of exposure (1 - exposure)."""
        exposure = 0.75

        complexity = scoring_service.calculate_complexity_score(exposure)

        assert complexity == pytest.approx(0.25, rel=0.01)

    def test_calculate_all_scores_for_role(self, scoring_service):
        """Should calculate all scores (exposure, impact, complexity, priority) for a role."""
        role_mapping = MagicMock(id="role-1", row_count=200)
        dwas = [
            MagicMock(ai_exposure_override=0.8),
            MagicMock(ai_exposure_override=0.6),
        ]

        scores = scoring_service.calculate_all_scores_for_role(
            role_mapping=role_mapping,
            selected_dwas=dwas,
            max_headcount=1000
        )

        assert "exposure" in scores
        assert "impact" in scores
        assert "complexity" in scores
        assert "priority" in scores

        # Verify exposure = (0.8 + 0.6) / 2 = 0.7
        assert scores["exposure"] == pytest.approx(0.7, rel=0.01)

        # Verify complexity = 1 - 0.7 = 0.3
        assert scores["complexity"] == pytest.approx(0.3, rel=0.01)

        # Verify impact = (200 * 0.7) / 1000 = 0.14
        assert scores["impact"] == pytest.approx(0.14, rel=0.01)

        # Verify priority = (0.7 * 0.4) + (0.14 * 0.4) + ((1 - 0.3) * 0.2)
        # = 0.28 + 0.056 + 0.14 = 0.476
        assert scores["priority"] == pytest.approx(0.476, rel=0.01)
