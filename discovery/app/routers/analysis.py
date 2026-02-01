"""Analysis router for the Discovery module."""
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
    ScoringService,
    get_analysis_service,
    get_scoring_service,
)


router = APIRouter(
    prefix="/discovery",
    tags=["discovery-analysis"],
)


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
        priority_tier=PriorityTier(data["priority_tier"]),
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
    description="Triggers scoring analysis for a discovery session.",
)
async def trigger_analysis(
    session_id: UUID,
    service: AnalysisService = Depends(get_analysis_service),
) -> TriggerAnalysisResponse:
    """Trigger scoring analysis for a session."""
    result = await service.trigger_analysis(session_id=session_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID {session_id} not found",
        )

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
