"""Handoff router for the Discovery module."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.handoff import (
    HandoffError,
    HandoffRequest,
    HandoffResponse,
    HandoffStatus,
    ValidationResult,
)
from app.services.handoff_service import (
    HandoffService,
    get_handoff_service,
)


router = APIRouter(
    prefix="/discovery",
    tags=["discovery-handoff"],
)


@router.post(
    "/sessions/{session_id}/handoff",
    response_model=HandoffResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": HandoffError, "description": "Validation failed"},
        404: {"description": "Session not found"},
    },
    summary="Submit candidates to intake",
    description="Submit discovery candidates to the intake system for processing.",
)
async def submit_handoff(
    session_id: UUID,
    request: HandoffRequest,
    service: HandoffService = Depends(get_handoff_service),
) -> HandoffResponse:
    """Submit candidates to intake system."""
    # First validate readiness
    validation_result = await service.validate_readiness(session_id)

    if validation_result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID {session_id} not found",
        )

    if not validation_result.is_ready:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "detail": "Handoff validation failed",
                "errors": validation_result.errors,
            },
        )

    # Proceed with submission
    result = await service.submit_to_intake(session_id, request)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID {session_id} not found",
        )

    return result


@router.post(
    "/sessions/{session_id}/handoff/validate",
    response_model=ValidationResult,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"description": "Session not found"},
    },
    summary="Validate handoff readiness",
    description="Check if the discovery session is ready for handoff to intake.",
)
async def validate_handoff(
    session_id: UUID,
    service: HandoffService = Depends(get_handoff_service),
) -> ValidationResult:
    """Check readiness for handoff."""
    result = await service.validate_readiness(session_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID {session_id} not found",
        )

    return result


@router.get(
    "/sessions/{session_id}/handoff",
    response_model=HandoffStatus,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"description": "Session not found"},
    },
    summary="Get handoff status",
    description="Get the current handoff status for a discovery session.",
)
async def get_handoff_status(
    session_id: UUID,
    service: HandoffService = Depends(get_handoff_service),
) -> HandoffStatus:
    """Get handoff status."""
    result = await service.get_status(session_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID {session_id} not found",
        )

    return result
