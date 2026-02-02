# discovery/app/services/analysis_service.py
"""Analysis service for scoring and aggregation."""
from typing import Any, Optional
from uuid import UUID

from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.role_mapping_repository import RoleMappingRepository
from app.repositories.activity_selection_repository import ActivitySelectionRepository
from app.services.scoring_engine import ScoringEngine
from app.schemas.analysis import AnalysisDimension, PriorityTier
from app.models.discovery_analysis import AnalysisDimension as DBDimension


class AnalysisService:
    """Service for analysis and scoring operations."""

    def __init__(
        self,
        analysis_repository: AnalysisRepository,
        role_mapping_repository: RoleMappingRepository | None = None,
        activity_selection_repository: ActivitySelectionRepository | None = None,
        scoring_engine: ScoringEngine | None = None,
    ) -> None:
        self.analysis_repository = analysis_repository
        self.role_mapping_repository = role_mapping_repository
        self.activity_selection_repository = activity_selection_repository
        self.scoring_engine = scoring_engine or ScoringEngine()

    async def trigger_analysis(self, session_id: UUID) -> dict[str, Any] | None:
        """Trigger scoring analysis for a session.

        Calculates scores for all role mappings and stores results.
        """
        if not self.role_mapping_repository or not self.activity_selection_repository:
            return {"status": "error", "message": "Missing dependencies"}

        # Get all role mappings
        mappings = await self.role_mapping_repository.get_for_session(session_id)
        if not mappings:
            return {"status": "error", "message": "No mappings found"}

        # Calculate total rows
        total_rows = sum(m.row_count or 0 for m in mappings)

        results_to_save = []
        for mapping in mappings:
            # Get selected DWAs for this mapping
            selections = await self.activity_selection_repository.get_for_role_mapping(
                mapping.id
            )
            selected_dwas = [s for s in selections if s.selected]

            # For now, use placeholder exposure scores (would come from DWA model)
            dwa_scores = [0.7] * len(selected_dwas) if selected_dwas else [0.5]

            # Calculate scores
            scores = self.scoring_engine.score_role(
                dwa_scores=dwa_scores,
                row_count=mapping.row_count or 0,
                total_rows=total_rows,
            )

            priority_tier = self.scoring_engine.classify_priority_tier(
                scores["priority"], scores["complexity"]
            )

            results_to_save.append({
                "session_id": session_id,
                "role_mapping_id": mapping.id,
                "dimension": DBDimension.ROLE,
                "dimension_value": mapping.source_role,
                "ai_exposure_score": scores["ai_exposure"],
                "impact_score": scores["impact"],
                "complexity_score": scores["complexity"],
                "priority_score": scores["priority"],
                "breakdown": {
                    "dwa_count": len(selected_dwas),
                    "priority_tier": priority_tier,
                },
            })

        await self.analysis_repository.save_results(results_to_save)
        return {"status": "completed", "count": len(results_to_save)}

    async def get_by_dimension(
        self,
        session_id: UUID,
        dimension: AnalysisDimension,
        priority_tier: PriorityTier | None = None,
    ) -> dict[str, Any] | None:
        """Get analysis results for a dimension."""
        # Map schema dimension to DB dimension
        dimension_map = {
            AnalysisDimension.ROLE: DBDimension.ROLE,
            AnalysisDimension.DEPARTMENT: DBDimension.DEPARTMENT,
            AnalysisDimension.LOB: DBDimension.LOB,
            AnalysisDimension.GEOGRAPHY: DBDimension.GEOGRAPHY,
            AnalysisDimension.TASK: DBDimension.TASK,
        }
        db_dimension = dimension_map.get(dimension, DBDimension.ROLE)

        results = await self.analysis_repository.get_for_session(
            session_id, db_dimension
        )

        if not results:
            return {"dimension": dimension.value, "results": []}

        formatted = []
        for r in results:
            tier = r.breakdown.get("priority_tier") if r.breakdown else None
            if priority_tier and tier != priority_tier.value:
                continue

            formatted.append({
                "id": str(r.id),
                "name": r.dimension_value,
                "ai_exposure_score": r.ai_exposure_score,
                "impact_score": r.impact_score,
                "complexity_score": r.complexity_score,
                "priority_score": r.priority_score,
                "priority_tier": tier,
            })

        return {"dimension": dimension.value, "results": formatted}

    async def get_all_dimensions(self, session_id: UUID) -> dict[str, Any] | None:
        """Get summary of all dimensions."""
        results = await self.analysis_repository.get_for_session(session_id)

        if not results:
            return None

        # Group by dimension
        by_dimension: dict[str, list] = {}
        for r in results:
            dim = r.dimension.value
            if dim not in by_dimension:
                by_dimension[dim] = []
            by_dimension[dim].append(r.ai_exposure_score)

        summary = {}
        for dim, scores in by_dimension.items():
            summary[dim] = {
                "count": len(scores),
                "avg_exposure": round(sum(scores) / len(scores), 3) if scores else 0,
            }

        return summary


class ScoringService:
    """Scoring service wrapper for ScoringEngine.

    Provides async interface for session-level scoring operations.
    """

    def __init__(self, scoring_engine: ScoringEngine | None = None) -> None:
        self.engine = scoring_engine or ScoringEngine()

    async def score_session(self, session_id: UUID) -> Optional[dict]:
        """Score all entities in a session.

        Note: Use AnalysisService.trigger_analysis() for full scoring workflow.
        This method is a placeholder for direct scoring API.
        """
        return {"status": "use_analysis_service"}


from collections.abc import AsyncGenerator


async def get_analysis_service() -> AsyncGenerator[AnalysisService, None]:
    """Get analysis service dependency for FastAPI.

    Yields a fully configured AnalysisService with repositories and scoring engine.
    """
    from app.models.base import async_session_maker

    async with async_session_maker() as db:
        analysis_repository = AnalysisRepository(db)
        role_mapping_repository = RoleMappingRepository(db)
        activity_selection_repository = ActivitySelectionRepository(db)
        scoring_engine = ScoringEngine()
        service = AnalysisService(
            analysis_repository=analysis_repository,
            role_mapping_repository=role_mapping_repository,
            activity_selection_repository=activity_selection_repository,
            scoring_engine=scoring_engine,
        )
        yield service


def get_scoring_service() -> ScoringService:
    """Dependency to get scoring service."""
    return ScoringService()
