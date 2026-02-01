"""Discovery analysis result repository for database operations.

Provides the DiscoveryAnalysisResultRepository for managing analysis result
records including CRUD operations and score-based queries.
"""

from uuid import UUID

from sqlalchemy import and_, delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.discovery.enums import AnalysisDimension
from app.modules.discovery.models.session import DiscoveryAnalysisResult


def _validate_score(score: float | None, field_name: str, allow_none: bool = True) -> None:
    """Validate that a score is within valid range.

    Args:
        score: Score to validate.
        field_name: Name of the score field for error messages.
        allow_none: Whether None is a valid value.

    Raises:
        ValueError: If score is outside the valid range (0.0-1.0).
    """
    if score is None:
        if not allow_none:
            raise ValueError(f"{field_name} is required")
        return
    if score < 0.0 or score > 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0, got {score}")


class DiscoveryAnalysisResultRepository:
    """Repository for DiscoveryAnalysisResult CRUD and query operations.

    Provides async database operations for analysis results including:
    - Create new analysis results with scores
    - Retrieve results by ID, session, dimension, or role mapping
    - Update scores and breakdown JSON
    - Get top results by priority score
    - Delete results individually or by session
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy async session for database operations.
        """
        self.session = session

    async def create(
        self,
        session_id: UUID,
        role_mapping_id: UUID,
        dimension: AnalysisDimension,
        dimension_value: str,
        ai_exposure_score: float,
        impact_score: float | None = None,
        complexity_score: float | None = None,
        priority_score: float | None = None,
        breakdown: dict | None = None,
    ) -> DiscoveryAnalysisResult:
        """Create a new analysis result.

        Creates an analysis result for a role mapping along a specific dimension.

        Args:
            session_id: UUID of the discovery session this result belongs to.
            role_mapping_id: UUID of the role mapping this result is for.
            dimension: The analysis dimension (e.g., ROLE, TASK, LOB).
            dimension_value: The specific value within the dimension.
            ai_exposure_score: AI exposure score (0.0-1.0).
            impact_score: Optional impact score (0.0-1.0).
            complexity_score: Optional complexity score (0.0-1.0).
            priority_score: Optional priority score (0.0-1.0).
            breakdown: Optional JSON breakdown of score components.

        Returns:
            The created DiscoveryAnalysisResult instance.

        Raises:
            ValueError: If any score is outside the range 0.0-1.0.
        """
        _validate_score(ai_exposure_score, "ai_exposure_score", allow_none=False)
        _validate_score(impact_score, "impact_score", allow_none=True)
        _validate_score(complexity_score, "complexity_score", allow_none=True)
        _validate_score(priority_score, "priority_score", allow_none=True)

        result = DiscoveryAnalysisResult(
            session_id=session_id,
            role_mapping_id=role_mapping_id,
            dimension=dimension,
            dimension_value=dimension_value,
            ai_exposure_score=ai_exposure_score,
            impact_score=impact_score,
            complexity_score=complexity_score,
            priority_score=priority_score,
            breakdown=breakdown,
        )
        self.session.add(result)
        await self.session.commit()
        await self.session.refresh(result)
        return result

    async def get_by_id(self, result_id: UUID) -> DiscoveryAnalysisResult | None:
        """Retrieve an analysis result by its ID.

        Args:
            result_id: UUID of the result to retrieve.

        Returns:
            DiscoveryAnalysisResult if found, None otherwise.
        """
        stmt = select(DiscoveryAnalysisResult).where(
            DiscoveryAnalysisResult.id == result_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_session_id(
        self, session_id: UUID
    ) -> list[DiscoveryAnalysisResult]:
        """Retrieve all analysis results for a specific session.

        Args:
            session_id: UUID of the session whose results to retrieve.

        Returns:
            List of DiscoveryAnalysisResult instances for the session.
        """
        stmt = select(DiscoveryAnalysisResult).where(
            DiscoveryAnalysisResult.session_id == session_id
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_dimension(
        self, session_id: UUID, dimension: AnalysisDimension
    ) -> list[DiscoveryAnalysisResult]:
        """Retrieve results filtered by dimension for a session.

        Args:
            session_id: UUID of the session to search in.
            dimension: The analysis dimension to filter by.

        Returns:
            List of DiscoveryAnalysisResult instances matching the dimension.
        """
        stmt = select(DiscoveryAnalysisResult).where(
            and_(
                DiscoveryAnalysisResult.session_id == session_id,
                DiscoveryAnalysisResult.dimension == dimension,
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_role_mapping_id(
        self, role_mapping_id: UUID
    ) -> list[DiscoveryAnalysisResult]:
        """Retrieve all analysis results for a specific role mapping.

        Args:
            role_mapping_id: UUID of the role mapping whose results to retrieve.

        Returns:
            List of DiscoveryAnalysisResult instances for the role mapping.
        """
        stmt = select(DiscoveryAnalysisResult).where(
            DiscoveryAnalysisResult.role_mapping_id == role_mapping_id
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_scores(
        self,
        result_id: UUID,
        ai_exposure_score: float | None = None,
        impact_score: float | None = None,
        complexity_score: float | None = None,
        priority_score: float | None = None,
    ) -> DiscoveryAnalysisResult | None:
        """Update score fields for an analysis result.

        Updates only the specified scores; unspecified scores remain unchanged.

        Args:
            result_id: UUID of the result to update.
            ai_exposure_score: New AI exposure score (0.0-1.0), or None to keep current.
            impact_score: New impact score (0.0-1.0), or None to keep current.
            complexity_score: New complexity score (0.0-1.0), or None to keep current.
            priority_score: New priority score (0.0-1.0), or None to keep current.

        Returns:
            Updated DiscoveryAnalysisResult if found, None otherwise.

        Raises:
            ValueError: If any score is outside the range 0.0-1.0.
        """
        # Validate scores before fetching to fail fast
        _validate_score(ai_exposure_score, "ai_exposure_score", allow_none=True)
        _validate_score(impact_score, "impact_score", allow_none=True)
        _validate_score(complexity_score, "complexity_score", allow_none=True)
        _validate_score(priority_score, "priority_score", allow_none=True)

        result = await self.get_by_id(result_id)
        if result is None:
            return None

        if ai_exposure_score is not None:
            result.ai_exposure_score = ai_exposure_score
        if impact_score is not None:
            result.impact_score = impact_score
        if complexity_score is not None:
            result.complexity_score = complexity_score
        if priority_score is not None:
            result.priority_score = priority_score

        await self.session.commit()
        await self.session.refresh(result)
        return result

    async def update_breakdown(
        self, result_id: UUID, breakdown: dict
    ) -> DiscoveryAnalysisResult | None:
        """Update the breakdown JSON for an analysis result.

        Args:
            result_id: UUID of the result to update.
            breakdown: New breakdown dictionary.

        Returns:
            Updated DiscoveryAnalysisResult if found, None otherwise.
        """
        result = await self.get_by_id(result_id)
        if result is None:
            return None

        result.breakdown = breakdown
        await self.session.commit()
        await self.session.refresh(result)
        return result

    async def get_top_by_priority(
        self, session_id: UUID, limit: int
    ) -> list[DiscoveryAnalysisResult]:
        """Get top N results by priority_score descending.

        Args:
            session_id: UUID of the session to get results from.
            limit: Maximum number of results to return.

        Returns:
            List of DiscoveryAnalysisResult instances ordered by priority_score desc.
        """
        stmt = (
            select(DiscoveryAnalysisResult)
            .where(DiscoveryAnalysisResult.session_id == session_id)
            .order_by(desc(DiscoveryAnalysisResult.priority_score))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, result_id: UUID) -> bool:
        """Delete an analysis result by its ID.

        Args:
            result_id: UUID of the result to delete.

        Returns:
            True if the result was deleted, False if not found.
        """
        result = await self.get_by_id(result_id)
        if result is None:
            return False

        await self.session.delete(result)
        await self.session.commit()
        return True

    async def delete_by_session_id(self, session_id: UUID) -> int:
        """Delete all analysis results for a session.

        Args:
            session_id: UUID of the session whose results to delete.

        Returns:
            Number of results deleted.
        """
        stmt = delete(DiscoveryAnalysisResult).where(
            DiscoveryAnalysisResult.session_id == session_id
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount
