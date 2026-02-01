"""Activities router for the Discovery module."""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.schemas.activity import (
    ActivitySelectionUpdate,
    BulkSelectionRequest,
    BulkSelectionResponse,
    DWAResponse,
    GWAGroupResponse,
    SelectionCountResponse,
)
from app.services.activity_service import (
    ActivityService,
    get_activity_service,
)


router = APIRouter(
    prefix="/discovery",
    tags=["discovery-activities"],
)


def _dict_to_dwa_response(data: dict) -> DWAResponse:
    """Convert a dictionary to DWAResponse, handling UUID conversion.

    Args:
        data: Dictionary containing DWA data.

    Returns:
        DWAResponse instance.
    """
    return DWAResponse(
        id=UUID(data["id"]) if isinstance(data["id"], str) else data["id"],
        code=data["code"],
        title=data["title"],
        description=data.get("description"),
        selected=data["selected"],
        gwa_code=data["gwa_code"],
    )


def _dict_to_gwa_group_response(data: dict) -> GWAGroupResponse:
    """Convert a dictionary to GWAGroupResponse.

    Args:
        data: Dictionary containing GWA group data.

    Returns:
        GWAGroupResponse instance.
    """
    return GWAGroupResponse(
        gwa_code=data["gwa_code"],
        gwa_title=data["gwa_title"],
        dwas=[_dict_to_dwa_response(dwa) for dwa in data["dwas"]],
    )


@router.get(
    "/sessions/{session_id}/activities",
    response_model=List[GWAGroupResponse],
    status_code=status.HTTP_200_OK,
    summary="Get activities for session",
    description="Retrieves activities grouped by GWA for a specific discovery session.",
)
async def get_activities(
    session_id: UUID,
    include_unselected: bool = Query(
        default=True,
        description="Whether to include unselected activities",
    ),
    service: ActivityService = Depends(get_activity_service),
) -> List[GWAGroupResponse]:
    """Get all activities for a session grouped by GWA."""
    result = await service.get_activities_by_session(
        session_id=session_id,
        include_unselected=include_unselected,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID {session_id} not found",
        )

    return [_dict_to_gwa_group_response(item) for item in result]


@router.put(
    "/activities/{activity_id}",
    response_model=DWAResponse,
    status_code=status.HTTP_200_OK,
    summary="Update activity selection",
    description="Updates the selection status of a single activity.",
)
async def update_activity_selection(
    activity_id: UUID,
    update_data: ActivitySelectionUpdate,
    service: ActivityService = Depends(get_activity_service),
) -> DWAResponse:
    """Update the selection status of an activity."""
    result = await service.update_selection(
        activity_id=activity_id,
        selected=update_data.selected,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Activity with ID {activity_id} not found",
        )

    return _dict_to_dwa_response(result)


@router.post(
    "/sessions/{session_id}/activities/select",
    response_model=BulkSelectionResponse,
    status_code=status.HTTP_200_OK,
    summary="Bulk select/deselect activities",
    description="Bulk update selection status for multiple activities.",
)
async def bulk_select_activities(
    session_id: UUID,
    request: BulkSelectionRequest,
    service: ActivityService = Depends(get_activity_service),
) -> BulkSelectionResponse:
    """Bulk select or deselect activities."""
    result = await service.bulk_update_selection(
        session_id=session_id,
        activity_ids=request.activity_ids,
        selected=request.selected,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID {session_id} not found",
        )

    return BulkSelectionResponse(updated_count=result["updated_count"])


@router.get(
    "/sessions/{session_id}/activities/count",
    response_model=SelectionCountResponse,
    status_code=status.HTTP_200_OK,
    summary="Get selection count",
    description="Get selection count statistics for a session.",
)
async def get_selection_count(
    session_id: UUID,
    service: ActivityService = Depends(get_activity_service),
) -> SelectionCountResponse:
    """Get selection count statistics for a session."""
    result = await service.get_selection_count(session_id=session_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID {session_id} not found",
        )

    return SelectionCountResponse(
        total=result["total"],
        selected=result["selected"],
        unselected=result["unselected"],
    )
