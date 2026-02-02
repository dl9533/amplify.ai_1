# discovery/tests/unit/services/test_fuzzy_matcher.py
"""Unit tests for fuzzy matcher."""
import pytest


def test_fuzzy_matcher_exists():
    """Test FuzzyMatcher is importable."""
    from app.services.fuzzy_matcher import FuzzyMatcher
    assert FuzzyMatcher is not None


def test_exact_match():
    """Test exact match returns high score."""
    from app.services.fuzzy_matcher import FuzzyMatcher

    matcher = FuzzyMatcher()
    score = matcher.calculate_similarity("Software Developer", "Software Developer")
    assert score >= 0.95


def test_fuzzy_match():
    """Test fuzzy match returns reasonable score."""
    from app.services.fuzzy_matcher import FuzzyMatcher

    matcher = FuzzyMatcher()
    score = matcher.calculate_similarity("Software Engineer", "Software Developer")
    assert 0.6 <= score <= 0.9


def test_no_match():
    """Test unrelated strings return low score."""
    from app.services.fuzzy_matcher import FuzzyMatcher

    matcher = FuzzyMatcher()
    score = matcher.calculate_similarity("Accountant", "Software Developer")
    assert score < 0.5


def test_find_best_matches():
    """Test finding best matches from candidates."""
    from app.services.fuzzy_matcher import FuzzyMatcher

    matcher = FuzzyMatcher()
    candidates = [
        {"code": "15-1252.00", "title": "Software Developers"},
        {"code": "15-1251.00", "title": "Computer Programmers"},
        {"code": "13-2011.00", "title": "Accountants"},
    ]

    results = matcher.find_best_matches("Software Engineer", candidates, top_n=2)

    assert len(results) == 2
    assert results[0]["code"] == "15-1252.00"
    assert "score" in results[0]


def test_classify_confidence():
    """Test confidence classification."""
    from app.services.fuzzy_matcher import FuzzyMatcher

    matcher = FuzzyMatcher()
    assert matcher.classify_confidence(0.90) == "high"
    assert matcher.classify_confidence(0.70) == "medium"
    assert matcher.classify_confidence(0.40) == "low"
