"""Role mappings router for the Discovery module."""
from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.schemas.role_mapping import (
    BulkConfirmRequest,
    BulkConfirmResponse,
    BulkRemapRequest,
    BulkRemapResponse,
    CreateMappingsRequest,
    CreateMappingsResponse,
    GroupedMappingSummary,
    GroupedRoleMappingsResponse,
    LobGroup,
    OnetOccupation,
    OnetSearchResult,
    RoleMappingCompact,
    RoleMappingResponse,
    RoleMappingUpdate,
    RoleMappingWithReasoning,
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


@router.post(
    "/sessions/{session_id}/role-mappings/generate",
    response_model=CreateMappingsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Auto-generate role mappings from session upload",
    description="Automatically finds the session's upload and triggers LLM-powered role mapping. Use this when you don't have the upload_id handy.",
)
async def generate_role_mappings(
    session_id: UUID,
    force: bool = Query(
        default=False,
        description="If true, regenerate mappings even if they already exist",
    ),
    service: RoleMappingService = Depends(get_role_mapping_service),
) -> CreateMappingsResponse:
    """Auto-generate role mappings from the session's upload.

    This endpoint:
    1. Checks if mappings already exist (returns existing if not forced)
    2. Finds the most recent upload for the session
    3. Extracts the role column from column_mappings
    4. Triggers the LLM-powered role mapping process
    """
    # Check if mappings already exist for this session
    if not force:
        existing = await service.get_by_session_id(session_id)
        if existing:
            return CreateMappingsResponse(
                created_count=0,
                mappings=[
                    RoleMappingWithReasoning(
                        id=m["id"],
                        source_role=m["source_role"],
                        onet_code=m["onet_code"],
                        onet_title=m.get("onet_title"),
                        confidence_score=m["confidence_score"],
                        confidence_tier="HIGH" if m["confidence_score"] >= 0.85 else "MEDIUM" if m["confidence_score"] >= 0.6 else "LOW",
                        reasoning=None,
                        is_confirmed=m["is_confirmed"],
                    )
                    for m in existing
                ],
            )

    if not service.upload_service:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Upload service not configured",
        )

    # If force=true, delete existing mappings first
    if force:
        await service.repository.delete_for_session(session_id)

    # Find the most recent upload for this session
    uploads = await service.upload_service.repository.get_for_session(session_id)
    if not uploads:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No uploads found for this session. Please upload a file first.",
        )

    # Use the most recent upload
    upload = uploads[0]

    # Find the role column from column_mappings
    # Format is { "role": "Job Title", "department": "Department", ... }
    column_mappings = upload.column_mappings or {}
    role_column = column_mappings.get("role")

    if not role_column:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No role column mapped in upload. Please map a column to 'Role' first.",
        )

    # Create mappings using LLM agent
    result = await service.create_mappings_from_upload(
        session_id=session_id,
        upload_id=upload.id,
        role_column=role_column,
    )

    return CreateMappingsResponse(
        created_count=len(result),
        mappings=[
            RoleMappingWithReasoning(
                id=m["id"],
                source_role=m["source_role"],
                onet_code=m["onet_code"],
                onet_title=m["onet_title"],
                confidence_score=m["confidence_score"],
                confidence_tier=m["confidence_tier"],
                reasoning=m.get("reasoning"),
                is_confirmed=m["is_confirmed"],
            )
            for m in result
        ],
    )


@router.post(
    "/sessions/{session_id}/role-mappings",
    response_model=CreateMappingsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create role mappings from upload",
    description="Triggers LLM-powered role mapping for roles in the uploaded file. Extracts unique roles and maps them to O*NET occupations.",
)
async def create_role_mappings(
    session_id: UUID,
    request: CreateMappingsRequest,
    service: RoleMappingService = Depends(get_role_mapping_service),
) -> CreateMappingsResponse:
    """Create role mappings from uploaded workforce data.

    This endpoint triggers the LLM-powered role mapping process:
    1. Reads the uploaded file content
    2. Extracts unique role titles from the mapped role column
    3. Uses Claude to semantically map each role to O*NET occupations
    4. Persists the mappings with confidence scores and reasoning
    """
    # Get upload to find the role column mapping
    if not service.upload_service:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Upload service not configured",
        )

    upload = await service.upload_service.repository.get_by_id(request.upload_id)
    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Upload with ID {request.upload_id} not found",
        )

    if upload.session_id != session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload does not belong to this session",
        )

    # Find the role column from column_mappings
    # Format is { "role": "Job Title", "department": "Department", ... }
    column_mappings = upload.column_mappings or {}
    role_column = column_mappings.get("role")

    if not role_column:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No role column mapped in upload. Please map a column to 'Role' first.",
        )

    # Create mappings using LLM agent
    result = await service.create_mappings_from_upload(
        session_id=session_id,
        upload_id=request.upload_id,
        role_column=role_column,
    )

    return CreateMappingsResponse(
        created_count=len(result),
        mappings=[
            RoleMappingWithReasoning(
                id=m["id"],
                source_role=m["source_role"],
                onet_code=m["onet_code"],
                onet_title=m["onet_title"],
                confidence_score=m["confidence_score"],
                confidence_tier=m["confidence_tier"],
                reasoning=m.get("reasoning"),
                is_confirmed=m["is_confirmed"],
            )
            for m in result
        ],
    )


@router.get(
    "/sessions/{session_id}/role-mappings/grouped",
    response_model=GroupedRoleMappingsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get grouped role mappings for session",
    description="Retrieves role mappings grouped by Line of Business for aggregated review.",
)
async def get_grouped_mappings(
    session_id: UUID,
    service: RoleMappingService = Depends(get_role_mapping_service),
) -> GroupedRoleMappingsResponse:
    """Get role mappings grouped by LOB for aggregated review.

    Returns role mappings organized by Line of Business with summary statistics
    for each group, enabling efficient review of large datasets.
    """
    result = await service.get_grouped_mappings(session_id=session_id)

    return GroupedRoleMappingsResponse(
        session_id=UUID(result["session_id"]) if isinstance(result["session_id"], str) else result["session_id"],
        overall_summary=GroupedMappingSummary(**result["overall_summary"]),
        lob_groups=[
            LobGroup(
                lob=group["lob"],
                summary=GroupedMappingSummary(**group["summary"]),
                mappings=[
                    RoleMappingCompact(
                        id=UUID(m["id"]) if isinstance(m["id"], str) else m["id"],
                        source_role=m["source_role"],
                        onet_code=m.get("onet_code"),
                        onet_title=m.get("onet_title"),
                        confidence_score=m["confidence_score"],
                        is_confirmed=m["is_confirmed"],
                        employee_count=m["employee_count"],
                    )
                    for m in group["mappings"]
                ],
            )
            for group in result["lob_groups"]
        ],
        ungrouped_mappings=[
            RoleMappingCompact(
                id=UUID(m["id"]) if isinstance(m["id"], str) else m["id"],
                source_role=m["source_role"],
                onet_code=m.get("onet_code"),
                onet_title=m.get("onet_title"),
                confidence_score=m["confidence_score"],
                is_confirmed=m["is_confirmed"],
                employee_count=m["employee_count"],
            )
            for m in result["ungrouped_mappings"]
        ],
    )


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
    description="Confirms role mappings with confidence scores at or above the threshold. Optionally filter by LOB or specific mapping IDs.",
)
async def bulk_confirm_mappings(
    session_id: UUID,
    request: BulkConfirmRequest,
    service: RoleMappingService = Depends(get_role_mapping_service),
) -> BulkConfirmResponse:
    """Bulk confirm mappings above a confidence threshold.

    Supports filtering by LOB group or specific mapping IDs for grouped review.
    """
    result = await service.bulk_confirm(
        session_id=session_id,
        threshold=request.threshold,
        lob=request.lob,
        mapping_ids=request.mapping_ids,
    )

    return BulkConfirmResponse(confirmed_count=result["confirmed_count"])


@router.post(
    "/sessions/{session_id}/role-mappings/remap",
    response_model=BulkRemapResponse,
    status_code=status.HTTP_200_OK,
    summary="Bulk remap low-confidence roles",
    description="Re-maps low-confidence role mappings using LLM semantic analysis.",
)
async def bulk_remap_mappings(
    session_id: UUID,
    request: BulkRemapRequest,
    service: RoleMappingService = Depends(get_role_mapping_service),
) -> BulkRemapResponse:
    """Re-map low-confidence roles using LLM agent.

    This endpoint triggers the LLM-powered role mapping agent to re-analyze
    roles that have low confidence scores and provide improved mappings.
    """
    result = await service.bulk_remap(
        session_id=session_id,
        threshold=request.threshold,
        mapping_ids=request.mapping_ids,
    )

    return BulkRemapResponse(
        remapped_count=result["remapped_count"],
        mappings=[
            RoleMappingWithReasoning(
                id=m["id"],
                source_role=m["source_role"],
                onet_code=m["onet_code"],
                onet_title=m["onet_title"],
                confidence_score=m["confidence_score"],
                confidence_tier=m["confidence_tier"],
                reasoning=m["reasoning"],
                is_confirmed=m["is_confirmed"],
            )
            for m in result["mappings"]
        ],
    )


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
