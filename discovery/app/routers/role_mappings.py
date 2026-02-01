"""Role mappings router for the Discovery module."""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

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

    return [
        RoleMappingResponse(
            id=UUID(item["id"]) if isinstance(item["id"], str) else item["id"],
            source_role=item["source_role"],
            onet_code=item["onet_code"],
            onet_title=item["onet_title"],
            confidence_score=item["confidence_score"],
            is_confirmed=item["is_confirmed"],
        )
        for item in result
    ]


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

    return RoleMappingResponse(
        id=UUID(result["id"]) if isinstance(result["id"], str) else result["id"],
        source_role=result["source_role"],
        onet_code=result["onet_code"],
        onet_title=result["onet_title"],
        confidence_score=result["confidence_score"],
        is_confirmed=result["is_confirmed"],
    )


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
    code: str,
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
