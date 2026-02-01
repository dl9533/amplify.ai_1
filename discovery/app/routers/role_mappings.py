"""Role mappings router for the Discovery module."""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.schemas.role_mapping import (
    BulkConfirmRequest,
    BulkConfirmResponse,
    OnetOccupation,
    OnetSearchResult,
    RoleMappingResponse,
    RoleMappingUpdate,
)
from app.services.role_mapping_service import (
    OnetService,
    RoleMappingService,
    get_onet_service,
    get_role_mapping_service,
)


router = APIRouter(
    prefix="/discovery",
    tags=["discovery-role-mappings"],
)


def _dict_to_role_mapping_response(data: dict) -> RoleMappingResponse:
    """Convert a dictionary to RoleMappingResponse, handling UUID conversion.

    Args:
        data: Dictionary containing role mapping data.

    Returns:
        RoleMappingResponse instance.
    """
    return RoleMappingResponse(
        id=UUID(data["id"]) if isinstance(data["id"], str) else data["id"],
        source_role=data["source_role"],
        onet_code=data["onet_code"],
        onet_title=data["onet_title"],
        confidence_score=data["confidence_score"],
        is_confirmed=data["is_confirmed"],
    )


@router.get(
    "/sessions/{session_id}/role-mappings",
    response_model=List[RoleMappingResponse],
    status_code=status.HTTP_200_OK,
    summary="Get role mappings for session",
    description="Retrieves all role mappings for a specific discovery session.",
)
async def get_role_mappings(
    session_id: UUID,
    service: RoleMappingService = Depends(get_role_mapping_service),
) -> List[RoleMappingResponse]:
    """Get all role mappings for a session."""
    result = await service.get_by_session_id(session_id=session_id)

    return [_dict_to_role_mapping_response(item) for item in result]


@router.put(
    "/role-mappings/{mapping_id}",
    response_model=RoleMappingResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a role mapping",
    description="Updates a role mapping with new O*NET code/title or confirmation status.",
)
async def update_role_mapping(
    mapping_id: UUID,
    update_data: RoleMappingUpdate,
    service: RoleMappingService = Depends(get_role_mapping_service),
) -> RoleMappingResponse:
    """Update a role mapping."""
    result = await service.update(
        mapping_id=mapping_id,
        onet_code=update_data.onet_code,
        onet_title=update_data.onet_title,
        is_confirmed=update_data.is_confirmed,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role mapping with ID {mapping_id} not found",
        )

    return _dict_to_role_mapping_response(result)


@router.post(
    "/sessions/{session_id}/role-mappings/confirm",
    response_model=BulkConfirmResponse,
    status_code=status.HTTP_200_OK,
    summary="Bulk confirm role mappings",
    description="Confirms all role mappings with confidence scores at or above the threshold.",
)
async def bulk_confirm_mappings(
    session_id: UUID,
    request: BulkConfirmRequest,
    service: RoleMappingService = Depends(get_role_mapping_service),
) -> BulkConfirmResponse:
    """Bulk confirm mappings above a confidence threshold."""
    result = await service.bulk_confirm(
        session_id=session_id,
        threshold=request.threshold,
    )

    return BulkConfirmResponse(confirmed_count=result["confirmed_count"])


@router.get(
    "/onet/search",
    response_model=List[OnetSearchResult],
    status_code=status.HTTP_200_OK,
    summary="Search O*NET occupations",
    description="Searches O*NET database for occupations matching the query.",
)
async def search_onet(
    q: str = Query(
        ...,
        min_length=1,
        description="Search query for O*NET occupations",
    ),
    service: OnetService = Depends(get_onet_service),
) -> List[OnetSearchResult]:
    """Search O*NET occupations."""
    result = await service.search(query=q)

    return [
        OnetSearchResult(
            code=item["code"],
            title=item["title"],
            score=item["score"],
        )
        for item in result
    ]


@router.get(
    "/onet/{code}",
    response_model=OnetOccupation,
    status_code=status.HTTP_200_OK,
    summary="Get O*NET occupation details",
    description="Retrieves detailed information about an O*NET occupation.",
)
async def get_onet_occupation(
    code: str = Path(
        ...,
        pattern=r"^\d{2}-\d{4}\.\d{2}$",
        description="O*NET SOC code in format XX-XXXX.XX (e.g., 15-1252.00)",
    ),
    service: OnetService = Depends(get_onet_service),
) -> OnetOccupation:
    """Get O*NET occupation details by code."""
    result = await service.get_occupation(code=code)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"O*NET occupation with code {code} not found",
        )

    return OnetOccupation(
        code=result["code"],
        title=result["title"],
        description=result.get("description"),
        gwas=result.get("gwas"),
    )
