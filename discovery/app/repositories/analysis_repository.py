"""Discovery analysis repository."""
from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.discovery_analysis import DiscoveryAnalysisResult, AnalysisDimension


class AnalysisRepository:
    """Repository for analysis results operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save_results(
        self,
        results: list[dict],
    ) -> Sequence[DiscoveryAnalysisResult]:
        """Save multiple analysis results."""
        db_results = []
        for r in results:
            # Convert string dimension to enum if needed
            if isinstance(r.get("dimension"), str):
                r["dimension"] = AnalysisDimension(r["dimension"])
            db_results.append(DiscoveryAnalysisResult(**r))

        self.session.add_all(db_results)
        await self.session.commit()
        for result in db_results:
            await self.session.refresh(result)
        return db_results

    async def get_for_session(
        self,
        session_id: UUID,
        dimension: AnalysisDimension | None = None,
    ) -> Sequence[DiscoveryAnalysisResult]:
        """Get analysis results for a session, optionally filtered by dimension."""
        stmt = select(DiscoveryAnalysisResult).where(
            DiscoveryAnalysisResult.session_id == session_id
        )
        if dimension:
            stmt = stmt.where(DiscoveryAnalysisResult.dimension == dimension)
        stmt = stmt.order_by(DiscoveryAnalysisResult.priority_score.desc())

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_role_mapping(
        self,
        role_mapping_id: UUID,
    ) -> Sequence[DiscoveryAnalysisResult]:
        """Get analysis results for a specific role mapping."""
        stmt = (
            select(DiscoveryAnalysisResult)
            .where(DiscoveryAnalysisResult.role_mapping_id == role_mapping_id)
            .order_by(DiscoveryAnalysisResult.dimension)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
