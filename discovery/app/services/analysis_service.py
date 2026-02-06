# discovery/app/services/analysis_service.py
"""Analysis service for scoring and aggregation."""
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.role_mapping_repository import RoleMappingRepository
from app.repositories.activity_selection_repository import ActivitySelectionRepository
from app.repositories.task_selection_repository import TaskSelectionRepository
from app.repositories.onet_repository import OnetRepository
from app.services.scoring_engine import ScoringEngine
from app.schemas.analysis import AnalysisDimension, PriorityTier
from app.models.discovery_analysis import AnalysisDimension as DBDimension
from app.models.onet_work_activities import OnetDWA, OnetIWA, OnetGWA


class AnalysisService:
    """Service for analysis and scoring operations."""

    def __init__(
        self,
        analysis_repository: AnalysisRepository,
        role_mapping_repository: RoleMappingRepository | None = None,
        activity_selection_repository: ActivitySelectionRepository | None = None,
        task_selection_repository: TaskSelectionRepository | None = None,
        onet_repository: OnetRepository | None = None,
        scoring_engine: ScoringEngine | None = None,
        db: AsyncSession | None = None,
    ) -> None:
        self.analysis_repository = analysis_repository
        self.role_mapping_repository = role_mapping_repository
        self.activity_selection_repository = activity_selection_repository
        self.task_selection_repository = task_selection_repository
        self.onet_repository = onet_repository
        self.scoring_engine = scoring_engine or ScoringEngine()
        self.db = db

    async def _get_dwa_exposure_scores(
        self,
        dwa_ids: list[str],
    ) -> list[float]:
        """Get AI exposure scores for DWAs from the O*NET hierarchy.

        For each DWA, uses ai_exposure_override if set, otherwise
        inherits from the parent GWA's ai_exposure_score.

        Args:
            dwa_ids: List of DWA IDs to get scores for.

        Returns:
            List of exposure scores (0-1). Returns 0.5 for missing data.
        """
        if not self.db or not dwa_ids:
            return [0.5] * len(dwa_ids) if dwa_ids else [0.5]

        # Query DWA -> IWA -> GWA to get exposure scores
        stmt = (
            select(
                OnetDWA.id,
                OnetDWA.ai_exposure_override,
                OnetGWA.ai_exposure_score,
            )
            .select_from(OnetDWA)
            .join(OnetIWA, OnetDWA.iwa_id == OnetIWA.id)
            .join(OnetGWA, OnetIWA.gwa_id == OnetGWA.id)
            .where(OnetDWA.id.in_(dwa_ids))
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        # Build lookup of DWA ID -> exposure score
        score_lookup: dict[str, float] = {}
        for row in rows:
            # Use DWA override if available, otherwise GWA score
            if row.ai_exposure_override is not None:
                score_lookup[row.id] = row.ai_exposure_override
            elif row.ai_exposure_score is not None:
                score_lookup[row.id] = row.ai_exposure_score
            else:
                score_lookup[row.id] = 0.5  # Default if no score available

        # Return scores in order of input dwa_ids
        return [score_lookup.get(dwa_id, 0.5) for dwa_id in dwa_ids]

    async def trigger_analysis(self, session_id: UUID) -> dict[str, Any] | None:
        """Trigger scoring analysis for a session.

        Calculates scores for all role mappings and stores results.
        Uses real AI exposure scores from O*NET GWA/DWA data.
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

            # Get real AI exposure scores from O*NET hierarchy
            if selected_dwas:
                dwa_ids = [s.dwa_id for s in selected_dwas]
                dwa_scores = await self._get_dwa_exposure_scores(dwa_ids)
            else:
                dwa_scores = [0.5]  # Default when no activities selected

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
                    "dwa_scores": dwa_scores[:5],  # Include first 5 for debugging
                },
            })

        await self.analysis_repository.save_results(results_to_save)
        return {"status": "completed", "count": len(results_to_save)}

    async def trigger_analysis_from_tasks(
        self, session_id: UUID
    ) -> dict[str, Any] | None:
        """Trigger scoring analysis for a session using task selections.

        Uses Task → DWA mapping to derive DWA exposure scores.
        This is the preferred method when using task-based workflows.
        """
        if (
            not self.role_mapping_repository
            or not self.task_selection_repository
            or not self.onet_repository
        ):
            return {"status": "error", "message": "Missing dependencies"}

        # Get all role mappings
        mappings = await self.role_mapping_repository.get_for_session(session_id)
        if not mappings:
            return {"status": "error", "message": "No mappings found"}

        # Calculate total rows
        total_rows = sum(m.row_count or 0 for m in mappings)

        results_to_save = []
        for mapping in mappings:
            # Get selected tasks for this mapping
            selections = await self.task_selection_repository.get_for_role_mapping(
                mapping.id
            )
            selected_tasks = [s for s in selections if s.selected]

            # Get DWA IDs for the selected tasks
            if selected_tasks:
                task_ids = [s.task_id for s in selected_tasks]
                task_to_dwas = await self.onet_repository.get_dwas_for_tasks(task_ids)

                # Flatten to unique DWA IDs
                dwa_ids = list(
                    set(
                        dwa_id
                        for dwa_list in task_to_dwas.values()
                        for dwa_id in dwa_list
                    )
                )

                # Get exposure scores for the DWAs
                if dwa_ids:
                    dwa_scores = await self._get_dwa_exposure_scores(dwa_ids)
                else:
                    dwa_scores = [0.5]  # Default when no DWAs mapped
            else:
                dwa_scores = [0.5]  # Default when no tasks selected
                dwa_ids = []

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
                    "task_count": len(selected_tasks),
                    "dwa_count": len(dwa_ids),
                    "priority_tier": priority_tier,
                    "dwa_scores": dwa_scores[:5],  # Include first 5 for debugging
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
        task_selection_repository = TaskSelectionRepository(db)
        onet_repository = OnetRepository(db)
        scoring_engine = ScoringEngine()
        service = AnalysisService(
            analysis_repository=analysis_repository,
            role_mapping_repository=role_mapping_repository,
            activity_selection_repository=activity_selection_repository,
            task_selection_repository=task_selection_repository,
            onet_repository=onet_repository,
            scoring_engine=scoring_engine,
            db=db,  # Pass db session for DWA exposure queries
        )
        yield service


def get_scoring_service() -> ScoringService:
    """Dependency to get scoring service."""
    return ScoringService()
