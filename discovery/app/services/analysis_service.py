"""Analysis and scoring services for the Discovery module."""
from typing import Optional
from uuid import UUID

from app.schemas.analysis import AnalysisDimension, PriorityTier


class AnalysisService:
    """Analysis service for managing analysis results.

    This is a placeholder service that will be replaced with actual
    database operations in a later task.
    """

    async def trigger_analysis(
        self,
        session_id: UUID,
    ) -> Optional[dict]:
        """Trigger scoring analysis for a session.

        Args:
            session_id: The session ID to trigger analysis for.

        Returns:
            Dict with status "processing", or None if session not found.

        Raises:
            NotImplementedError: Service not implemented.
        """
        raise NotImplementedError("Service not implemented")

    async def get_by_dimension(
        self,
        session_id: UUID,
        dimension: AnalysisDimension,
        priority_tier: Optional[PriorityTier] = None,
    ) -> Optional[dict]:
        """Get analysis results for a specific dimension.

        Args:
            session_id: The session ID to get analysis for.
            dimension: The analysis dimension to filter by.
            priority_tier: Optional priority tier to filter results.

        Returns:
            Dict with dimension and results list, or None if analysis not found.
            Each result contains: id, name, ai_exposure_score, impact_score,
            complexity_score, priority_score, and priority_tier.

        Raises:
            NotImplementedError: Service not implemented.
        """
        raise NotImplementedError("Service not implemented")

    async def get_all_dimensions(
        self,
        session_id: UUID,
    ) -> Optional[dict]:
        """Get summary of all dimensions for a session.

        Args:
            session_id: The session ID to get analysis summary for.

        Returns:
            Dict with dimension names as keys and summary stats as values.
            Each summary contains: count and avg_exposure.
            Returns None if session not found or analysis not run.

        Raises:
            NotImplementedError: Service not implemented.
        """
        raise NotImplementedError("Service not implemented")


class ScoringService:
    """Scoring service for computing analysis scores.

    This is a placeholder service that will be replaced with actual
    scoring logic in a later task.
    """

    async def score_session(
        self,
        session_id: UUID,
    ) -> Optional[dict]:
        """Score all entities in a session.

        Args:
            session_id: The session ID to score.

        Returns:
            Dict with scoring results, or None if session not found.

        Raises:
            NotImplementedError: Service not implemented.
        """
        raise NotImplementedError("Service not implemented")


def get_analysis_service() -> AnalysisService:
    """Dependency to get analysis service."""
    return AnalysisService()


def get_scoring_service() -> ScoringService:
    """Dependency to get scoring service."""
    return ScoringService()
