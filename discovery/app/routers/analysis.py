"""Analysis router for the Discovery module."""
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.schemas.analysis import (
    AllDimensionsResponse,
    AnalysisDimension,
    AnalysisResult,
    DimensionAnalysisResponse,
    DimensionSummary,
    PriorityTier,
    TriggerAnalysisResponse,
)
from app.services.analysis_service import (
    AnalysisService,
    get_analysis_service,
)
from app.services.roadmap_service import (
    RoadmapService,
    get_roadmap_service,
)

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/discovery",
    tags=["discovery-analysis"],
)


# Mapping from database priority tier values to schema values
# Database uses: now, next_quarter, future (from agentification_candidate model)
# Schema uses: HIGH, MEDIUM, LOW (for API responses)
DB_TO_SCHEMA_PRIORITY_TIER = {
    "now": PriorityTier.HIGH,
    "next_quarter": PriorityTier.MEDIUM,
    "future": PriorityTier.LOW,
    # Also handle if already in schema format
    "HIGH": PriorityTier.HIGH,
    "MEDIUM": PriorityTier.MEDIUM,
    "LOW": PriorityTier.LOW,
}


def _convert_priority_tier(db_value: str) -> PriorityTier:
    """Convert database priority tier to schema PriorityTier.

    Args:
        db_value: The priority tier value from the database.

    Returns:
        The corresponding schema PriorityTier enum value.
    """
    tier = DB_TO_SCHEMA_PRIORITY_TIER.get(db_value)
    if tier is None:
        # Default to LOW for unknown values
        return PriorityTier.LOW
    return tier


def _dict_to_analysis_result(data: dict) -> AnalysisResult:
    """Convert a dictionary to AnalysisResult, handling UUID conversion.

    Args:
        data: Dictionary containing analysis result data.

    Returns:
        AnalysisResult instance.
    """
    return AnalysisResult(
        id=UUID(data["id"]) if isinstance(data["id"], str) else data["id"],
        name=data["name"],
        ai_exposure_score=data["ai_exposure_score"],
        impact_score=data["impact_score"],
        complexity_score=data["complexity_score"],
        priority_score=data["priority_score"],
        priority_tier=_convert_priority_tier(data["priority_tier"]),
        row_count=data.get("row_count"),
    )


def _dict_to_dimension_summary(data: dict) -> DimensionSummary:
    """Convert a dictionary to DimensionSummary.

    Args:
        data: Dictionary containing dimension summary data.

    Returns:
        DimensionSummary instance.
    """
    return DimensionSummary(
        count=data["count"],
        avg_exposure=data["avg_exposure"],
    )


@router.post(
    "/sessions/{session_id}/analyze",
    response_model=TriggerAnalysisResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger analysis for session",
    description="Triggers scoring analysis for a discovery session and generates roadmap candidates. "
    "Use source='tasks' to analyze based on task selections (preferred), or 'activities' for "
    "legacy DWA-based analysis.",
)
async def trigger_analysis(
    session_id: UUID,
    source: str = Query(
        default="tasks",
        description="Analysis source: 'tasks' (recommended) or 'activities' (legacy DWA-based)",
    ),
    service: AnalysisService = Depends(get_analysis_service),
    roadmap_service: RoadmapService = Depends(get_roadmap_service),
) -> TriggerAnalysisResponse:
    """Trigger scoring analysis for a session and generate roadmap candidates."""
    if source == "tasks":
        result = await service.trigger_analysis_from_tasks(session_id=session_id)
    else:
        result = await service.trigger_analysis(session_id=session_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID {session_id} not found",
        )

    # Auto-generate roadmap candidates from analysis results
    if result.get("status") == "completed":
        try:
            candidates = await roadmap_service.generate_candidates(session_id=session_id)
            logger.info(f"Generated {len(candidates)} roadmap candidates for session {session_id}")
        except Exception as e:
            logger.error(f"Failed to generate candidates for session {session_id}: {e}")
            # Don't fail the analysis if candidate generation fails

    return TriggerAnalysisResponse(status=result["status"])


@router.get(
    "/sessions/{session_id}/analysis/{dimension}",
    response_model=DimensionAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Get analysis by dimension",
    description="Retrieves analysis results for a specific dimension.",
)
async def get_analysis_by_dimension(
    session_id: UUID,
    dimension: AnalysisDimension,
    priority_tier: Optional[PriorityTier] = Query(
        default=None,
        description="Filter results by priority tier (HIGH, MEDIUM, LOW)",
    ),
    service: AnalysisService = Depends(get_analysis_service),
) -> DimensionAnalysisResponse:
    """Get analysis results for a specific dimension."""
    result = await service.get_by_dimension(
        session_id=session_id,
        dimension=dimension,
        priority_tier=priority_tier,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis not found for session {session_id}. Run analysis first.",
        )

    return DimensionAnalysisResponse(
        dimension=AnalysisDimension(result["dimension"]),
        results=[_dict_to_analysis_result(r) for r in result["results"]],
    )


@router.get(
    "/sessions/{session_id}/analysis",
    response_model=AllDimensionsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get all dimensions analysis",
    description="Retrieves summary of analysis results for all dimensions.",
)
async def get_all_dimensions_analysis(
    session_id: UUID,
    service: AnalysisService = Depends(get_analysis_service),
) -> AllDimensionsResponse:
    """Get summary of all dimensions for a session."""
    result = await service.get_all_dimensions(session_id=session_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis not found for session {session_id}. Run analysis first.",
        )

    summaries = {
        key: _dict_to_dimension_summary(value) for key, value in result.items()
    }
    return AllDimensionsResponse(root=summaries)
