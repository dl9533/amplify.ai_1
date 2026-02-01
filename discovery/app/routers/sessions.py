"""Discovery session router with CRUD endpoints."""
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.schemas.session import (
    SessionCreate,
    SessionResponse,
    SessionList,
    StepUpdate,
)
from app.services.session_service import SessionService, get_session_service


router = APIRouter(
    prefix="/discovery/sessions",
    tags=["discovery-sessions"],
)


@router.post(
    "",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new discovery session",
    description="Creates a new discovery session for the specified organization.",
)
async def create_session(
    session_data: SessionCreate,
    service: SessionService = Depends(get_session_service),
) -> SessionResponse:
    """Create a new discovery session."""
    result = await service.create(organization_id=session_data.organization_id)

    return SessionResponse(
        id=UUID(result["id"]),
        status=result["status"],
        current_step=result["current_step"],
        created_at=datetime.fromisoformat(result["created_at"]),
        updated_at=datetime.fromisoformat(result["updated_at"]),
    )


@router.get(
    "/{session_id}",
    response_model=SessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a discovery session by ID",
    description="Retrieves details of a specific discovery session.",
)
async def get_session(
    session_id: UUID,
    service: SessionService = Depends(get_session_service),
) -> SessionResponse:
    """Get a discovery session by ID."""
    result = await service.get_by_id(session_id=session_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID {session_id} not found",
        )

    return SessionResponse(
        id=UUID(result["id"]),
        status=result["status"],
        current_step=result["current_step"],
        created_at=datetime.fromisoformat(result["created_at"]),
        updated_at=datetime.fromisoformat(result["updated_at"]),
    )


@router.get(
    "",
    response_model=SessionList,
    status_code=status.HTTP_200_OK,
    summary="List discovery sessions",
    description="Lists all discovery sessions for the current user with pagination.",
)
async def list_sessions(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    service: SessionService = Depends(get_session_service),
) -> SessionList:
    """List discovery sessions with pagination."""
    result = await service.list_for_user(page=page, per_page=per_page)

    items = [
        SessionResponse(
            id=UUID(item["id"]),
            status=item["status"],
            current_step=item["current_step"],
            created_at=datetime.fromisoformat(item["created_at"]),
            updated_at=datetime.fromisoformat(item["updated_at"]),
        )
        for item in result["items"]
    ]

    return SessionList(
        items=items,
        total=result["total"],
        page=result["page"],
        per_page=result["per_page"],
    )


@router.patch(
    "/{session_id}/step",
    response_model=SessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Update session step",
    description="Updates the current step of a discovery session.",
)
async def update_session_step(
    session_id: UUID,
    step_data: StepUpdate,
    service: SessionService = Depends(get_session_service),
) -> SessionResponse:
    """Update the current step of a discovery session."""
    result = await service.update_step(session_id=session_id, step=step_data.step)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID {session_id} not found",
        )

    return SessionResponse(
        id=UUID(result["id"]),
        status=result["status"],
        current_step=result["current_step"],
        created_at=datetime.fromisoformat(result["created_at"]),
        updated_at=datetime.fromisoformat(result["updated_at"]),
    )


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a discovery session",
    description="Deletes a discovery session by ID.",
)
async def delete_session(
    session_id: UUID,
    service: SessionService = Depends(get_session_service),
) -> None:
    """Delete a discovery session."""
    deleted = await service.delete(session_id=session_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID {session_id} not found",
        )
