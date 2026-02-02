# discovery/tests/unit/services/test_scoring_engine.py
"""Unit tests for scoring engine."""
import pytest


def test_scoring_engine_exists():
    """Test ScoringEngine is importable."""
    from app.services.scoring_engine import ScoringEngine
    assert ScoringEngine is not None


def test_calculate_ai_exposure():
    """Test AI exposure score calculation."""
    from app.services.scoring_engine import ScoringEngine

    engine = ScoringEngine()
    dwa_scores = [0.8, 0.7, 0.9, 0.6]
    result = engine.calculate_ai_exposure(dwa_scores)

    assert 0.7 <= result <= 0.8  # Average should be 0.75


def test_calculate_impact():
    """Test impact score calculation."""
    from app.services.scoring_engine import ScoringEngine

    engine = ScoringEngine()
    result = engine.calculate_impact(
        exposure=0.8,
        row_count=100,
        total_rows=1000,
    )

    assert 0.0 <= result <= 1.0


def test_calculate_complexity():
    """Test complexity score calculation."""
    from app.services.scoring_engine import ScoringEngine

    engine = ScoringEngine()
    result = engine.calculate_complexity(exposure=0.8)

    # Complexity is inverse of exposure
    assert result == pytest.approx(0.2, rel=0.01)


def test_calculate_priority():
    """Test priority score calculation."""
    from app.services.scoring_engine import ScoringEngine

    engine = ScoringEngine()
    result = engine.calculate_priority(
        exposure=0.8,
        impact=0.7,
        complexity=0.2,
    )

    # Priority = (0.8*0.4) + (0.7*0.4) + ((1-0.2)*0.2) = 0.32 + 0.28 + 0.16 = 0.76
    assert result == pytest.approx(0.76, rel=0.01)


def test_score_role():
    """Test complete role scoring."""
    from app.services.scoring_engine import ScoringEngine

    engine = ScoringEngine()
    result = engine.score_role(
        dwa_scores=[0.8, 0.7, 0.9],
        row_count=50,
        total_rows=500,
    )

    assert "ai_exposure" in result
    assert "impact" in result
    assert "complexity" in result
    assert "priority" in result


def test_classify_priority_tier_now():
    """Test classification into 'now' tier."""
    from app.services.scoring_engine import ScoringEngine

    engine = ScoringEngine()
    tier = engine.classify_priority_tier(priority=0.85, complexity=0.2)
    assert tier == "now"


def test_classify_priority_tier_next():
    """Test classification into 'next_quarter' tier."""
    from app.services.scoring_engine import ScoringEngine

    engine = ScoringEngine()
    tier = engine.classify_priority_tier(priority=0.65, complexity=0.5)
    assert tier == "next_quarter"


def test_classify_priority_tier_future():
    """Test classification into 'future' tier."""
    from app.services.scoring_engine import ScoringEngine

    engine = ScoringEngine()
    tier = engine.classify_priority_tier(priority=0.40, complexity=0.6)
    assert tier == "future"
