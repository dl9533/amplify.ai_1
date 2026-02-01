"""Discovery upload router for file upload endpoints."""
from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.schemas.upload import ColumnMappingUpdate, UploadResponse
from app.services.upload_service import UploadService, get_upload_service


# Constants for file validation
ALLOWED_CONTENT_TYPES = {
    "text/csv",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


router = APIRouter(
    prefix="/discovery",
    tags=["discovery-uploads"],
)


@router.post(
    "/sessions/{session_id}/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a file to a discovery session",
    description="Uploads a CSV or XLSX file and returns detected schema information.",
)
async def upload_file(
    session_id: UUID,
    file: UploadFile = File(...),
    service: UploadService = Depends(get_upload_service),
) -> UploadResponse:
    """Upload a file to a discovery session."""
    # Validate content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file.content_type}. Only CSV and XLSX files are accepted.",
        )

    # Read file content
    content = await file.read()

    # Validate file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024 * 1024)}MB.",
        )

    # Process the upload
    result = await service.process_upload(
        session_id=session_id,
        file_name=file.filename or "unknown",
        content=content,
    )

    return UploadResponse(
        id=UUID(result["id"]),
        file_name=result["file_name"],
        row_count=result["row_count"],
        detected_schema=result["detected_schema"],
        created_at=datetime.fromisoformat(result["created_at"]),
        column_mappings=result.get("column_mappings"),
    )


@router.get(
    "/sessions/{session_id}/uploads",
    response_model=List[UploadResponse],
    status_code=status.HTTP_200_OK,
    summary="List uploads for a session",
    description="Returns all uploads for the specified discovery session.",
)
async def list_uploads(
    session_id: UUID,
    service: UploadService = Depends(get_upload_service),
) -> List[UploadResponse]:
    """List all uploads for a discovery session."""
    results = await service.get_by_session_id(session_id=session_id)

    return [
        UploadResponse(
            id=UUID(item["id"]),
            file_name=item["file_name"],
            row_count=item["row_count"],
            detected_schema=item["detected_schema"],
            created_at=datetime.fromisoformat(item["created_at"]),
            column_mappings=item.get("column_mappings"),
        )
        for item in results
    ]


@router.put(
    "/uploads/{upload_id}/mappings",
    response_model=UploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Update column mappings for an upload",
    description="Updates the column mappings (role, department, geography) for an upload.",
)
async def update_mappings(
    upload_id: UUID,
    mappings: ColumnMappingUpdate,
    service: UploadService = Depends(get_upload_service),
) -> UploadResponse:
    """Update column mappings for an upload."""
    # Convert to dict, excluding None values
    mappings_dict = {
        k: v for k, v in mappings.model_dump().items() if v is not None
    }

    result = await service.update_column_mappings(
        upload_id=upload_id,
        mappings=mappings_dict,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Upload with ID {upload_id} not found",
        )

    return UploadResponse(
        id=UUID(result["id"]),
        file_name=result["file_name"],
        row_count=result["row_count"],
        detected_schema=result["detected_schema"],
        created_at=datetime.fromisoformat(result["created_at"]),
        column_mappings=result.get("column_mappings"),
    )
