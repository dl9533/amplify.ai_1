# discovery/app/services/fuzzy_matcher.py
"""Fuzzy string matching for role-to-occupation mapping."""
from difflib import SequenceMatcher
from typing import Any


class FuzzyMatcher:
    """Fuzzy string matcher for occupation matching."""

    def calculate_similarity(self, s1: str, s2: str) -> float:
        """Calculate similarity score between two strings.

        Uses SequenceMatcher ratio with normalization.

        Args:
            s1: First string.
            s2: Second string.

        Returns:
            Similarity score between 0.0 and 1.0.
        """
        s1_normalized = self._normalize(s1)
        s2_normalized = self._normalize(s2)

        # Direct ratio
        ratio = SequenceMatcher(None, s1_normalized, s2_normalized).ratio()

        # Bonus for substring match
        if s1_normalized in s2_normalized or s2_normalized in s1_normalized:
            ratio = min(1.0, ratio + 0.1)

        return ratio

    def _normalize(self, s: str) -> str:
        """Normalize string for comparison."""
        return s.lower().strip()

    def find_best_matches(
        self,
        query: str,
        candidates: list[dict[str, Any]],
        top_n: int = 5,
        title_key: str = "title",
    ) -> list[dict[str, Any]]:
        """Find best matching candidates for a query.

        Args:
            query: The search query.
            candidates: List of candidate dicts with title field.
            top_n: Number of top results to return.
            title_key: Key for the title field in candidates.

        Returns:
            List of candidates with added 'score' field, sorted by score.
        """
        scored = []
        for candidate in candidates:
            title = candidate.get(title_key, "")
            score = self.calculate_similarity(query, title)
            scored.append({**candidate, "score": round(score, 3)})

        # Sort by score descending
        scored.sort(key=lambda x: x["score"], reverse=True)

        return scored[:top_n]

    def classify_confidence(self, score: float) -> str:
        """Classify confidence level from score.

        Args:
            score: Similarity score 0.0-1.0.

        Returns:
            Confidence level: 'high', 'medium', 'low'.
        """
        if score >= 0.85:
            return "high"
        elif score >= 0.60:
            return "medium"
        else:
            return "low"
