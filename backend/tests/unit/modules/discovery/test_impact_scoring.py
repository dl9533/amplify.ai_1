# backend/tests/unit/modules/discovery/test_impact_scoring.py
import pytest
from unittest.mock import MagicMock

from app.modules.discovery.services.scoring import ScoringService


@pytest.fixture
def scoring_service():
    return ScoringService()


class TestImpactScoreCalculator:
    """Tests for impact score calculation: impact = role_count * exposure."""

    def test_impact_score_basic_calculation(self, scoring_service):
        """Impact should be role_count * exposure_score."""
        role_mapping = MagicMock(
            row_count=100,  # 100 employees in this role
        )
        exposure_score = 0.8

        impact = scoring_service.calculate_impact_score(
            role_mapping=role_mapping,
            exposure_score=exposure_score
        )

        # 100 * 0.8 = 80, normalized to 0-1 scale
        # Assuming max role count of 1000 for normalization
        assert impact == pytest.approx(0.08, rel=0.01)

    def test_impact_score_high_headcount(self, scoring_service):
        """High headcount should produce higher impact."""
        role_mapping_low = MagicMock(row_count=10)
        role_mapping_high = MagicMock(row_count=500)
        exposure = 0.7

        impact_low = scoring_service.calculate_impact_score(
            role_mapping=role_mapping_low,
            exposure_score=exposure
        )
        impact_high = scoring_service.calculate_impact_score(
            role_mapping=role_mapping_high,
            exposure_score=exposure
        )

        assert impact_high > impact_low

    def test_impact_score_high_exposure(self, scoring_service):
        """High exposure should produce higher impact."""
        role_mapping = MagicMock(row_count=100)

        impact_low = scoring_service.calculate_impact_score(
            role_mapping=role_mapping,
            exposure_score=0.2
        )
        impact_high = scoring_service.calculate_impact_score(
            role_mapping=role_mapping,
            exposure_score=0.9
        )

        assert impact_high > impact_low

    def test_impact_score_zero_headcount(self, scoring_service):
        """Zero headcount should return zero impact."""
        role_mapping = MagicMock(row_count=0)

        impact = scoring_service.calculate_impact_score(
            role_mapping=role_mapping,
            exposure_score=0.9
        )

        assert impact == 0.0

    def test_impact_score_zero_exposure(self, scoring_service):
        """Zero exposure should return zero impact."""
        role_mapping = MagicMock(row_count=100)

        impact = scoring_service.calculate_impact_score(
            role_mapping=role_mapping,
            exposure_score=0.0
        )

        assert impact == 0.0

    def test_impact_score_normalized_to_unit_interval(self, scoring_service):
        """Impact score should always be between 0 and 1."""
        role_mapping = MagicMock(row_count=5000)  # Very high headcount

        impact = scoring_service.calculate_impact_score(
            role_mapping=role_mapping,
            exposure_score=1.0
        )

        assert 0.0 <= impact <= 1.0

    def test_impact_score_with_custom_max_headcount(self, scoring_service):
        """Should allow custom max headcount for normalization."""
        role_mapping = MagicMock(row_count=500)

        impact = scoring_service.calculate_impact_score(
            role_mapping=role_mapping,
            exposure_score=1.0,
            max_headcount=500  # Custom max
        )

        assert impact == pytest.approx(1.0, rel=0.01)

    def test_calculate_impact_for_session(self, scoring_service):
        """Should calculate impact scores for all role mappings in a session."""
        role_mappings = [
            MagicMock(id="role-1", row_count=100),
            MagicMock(id="role-2", row_count=200),
            MagicMock(id="role-3", row_count=50),
        ]
        exposure_scores = {
            "role-1": 0.8,
            "role-2": 0.6,
            "role-3": 0.9,
        }

        impacts = scoring_service.calculate_impact_scores_for_session(
            role_mappings=role_mappings,
            exposure_scores=exposure_scores
        )

        assert len(impacts) == 3
        assert "role-1" in impacts
        assert "role-2" in impacts
        assert "role-3" in impacts
        # role-2 has highest raw impact (200 * 0.6 = 120)
        # role-1 has second (100 * 0.8 = 80)
        # role-3 has lowest (50 * 0.9 = 45)
