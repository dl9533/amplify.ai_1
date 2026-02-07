"""Roadmap router for the Discovery module."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.schemas.roadmap import (
    BulkUpdateRequest,
    BulkUpdateResponse,
    EstimatedEffort,
    PhaseUpdate,
    ReorderRequest,
    ReorderResponse,
    RoadmapItem,
    RoadmapItemsResponse,
    RoadmapPhase,
)
from app.services.roadmap_service import (
    RoadmapService,
    get_roadmap_service,
)


router = APIRouter(
    prefix="/discovery",
    tags=["discovery-roadmap"],
)


def _dict_to_roadmap_item(data: dict) -> RoadmapItem:
    """Convert a dictionary to RoadmapItem, handling type conversions.

    Args:
        data: Dictionary containing roadmap item data.

    Returns:
        RoadmapItem instance.
    """
    return RoadmapItem(
        id=UUID(data["id"]) if isinstance(data["id"], str) else data["id"],
        role_name=data["role_name"],
        priority_score=data["priority_score"],
        priority_tier=data["priority_tier"],
        phase=RoadmapPhase(data["phase"]),
        estimated_effort=EstimatedEffort(data["estimated_effort"]),
        order=data.get("order"),
        lob=data.get("lob"),
    )


@router.get(
    "/sessions/{session_id}/roadmap",
    response_model=RoadmapItemsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get roadmap items",
    description="Retrieves prioritized candidates (roadmap items) for a session.",
)
async def get_roadmap(
    session_id: UUID,
    phase: Optional[RoadmapPhase] = Query(
        default=None,
        description="Filter items by phase (NOW, NEXT, LATER)",
    ),
    service: RoadmapService = Depends(get_roadmap_service),
) -> RoadmapItemsResponse:
    """Get roadmap items for a session."""
    result = await service.get_roadmap(session_id=session_id, phase=phase)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID {session_id} not found",
        )

    return RoadmapItemsResponse(
        items=[_dict_to_roadmap_item(item) for item in result]
    )


@router.put(
    "/roadmap/{item_id}",
    response_model=RoadmapItem,
    status_code=status.HTTP_200_OK,
    summary="Update roadmap item phase",
    description="Updates a single roadmap item's phase.",
)
async def update_phase(
    item_id: UUID,
    body: PhaseUpdate,
    service: RoadmapService = Depends(get_roadmap_service),
) -> RoadmapItem:
    """Update a roadmap item's phase."""
    result = await service.update_phase(item_id=item_id, phase=body.phase)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Roadmap item with ID {item_id} not found",
        )

    return _dict_to_roadmap_item(result)


@router.post(
    "/sessions/{session_id}/roadmap/reorder",
    response_model=ReorderResponse,
    status_code=status.HTTP_200_OK,
    summary="Reorder roadmap items",
    description="Reorders roadmap items by providing an ordered list of IDs.",
)
async def reorder_roadmap(
    session_id: UUID,
    body: ReorderRequest,
    service: RoadmapService = Depends(get_roadmap_service),
) -> ReorderResponse:
    """Reorder roadmap items within a session."""
    result = await service.reorder(session_id=session_id, item_ids=body.item_ids)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID {session_id} not found",
        )

    return ReorderResponse(success=result)


@router.post(
    "/sessions/{session_id}/roadmap/bulk-update",
    response_model=BulkUpdateResponse,
    status_code=status.HTTP_200_OK,
    summary="Bulk update roadmap phases",
    description="Bulk update phases for multiple roadmap items.",
)
async def bulk_update_phases(
    session_id: UUID,
    body: BulkUpdateRequest,
    service: RoadmapService = Depends(get_roadmap_service),
) -> BulkUpdateResponse:
    """Bulk update phases for multiple roadmap items."""
    result = await service.bulk_update(session_id=session_id, updates=body.updates)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID {session_id} not found",
        )

    return BulkUpdateResponse(updated_count=result)
