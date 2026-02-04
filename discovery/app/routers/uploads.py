"""Discovery upload router for file upload endpoints."""
import os
import re
from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.schemas.upload import ColumnMappingUpdate, DetectedMappingResponse, UploadResponse
from app.services.column_detection_service import ColumnDetectionService
from app.services.upload_service import UploadService, get_upload_service


# Constants for file validation
ALLOWED_CONTENT_TYPES = {
    "text/csv",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Magic bytes for XLSX files (PK signature for ZIP-based formats)
XLSX_MAGIC_BYTES = (b"PK\x03\x04", b"PK\x05\x06")


def _validate_file_content(content: bytes, content_type: str) -> bool:
    """
    Validate file content matches claimed content type using magic bytes.

    Args:
        content: The file content bytes
        content_type: The claimed MIME type (base type without charset)

    Returns:
        True if content matches the claimed type

    Raises:
        HTTPException: If content does not match claimed type
    """
    if content_type == "text/csv":
        # CSV should be text - check for printable ASCII or UTF-8 BOM
        if not content:
            return True  # Empty files handled elsewhere
        # Check for UTF-8 BOM
        if content.startswith(b"\xef\xbb\xbf"):
            return True
        # Check first 1024 bytes for printable ASCII/UTF-8
        sample = content[:1024]
        try:
            sample.decode("utf-8")
            return True
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File content does not appear to be valid CSV text.",
            )
    elif content_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        # XLSX files are ZIP-based and should start with PK signature
        if not content:
            return True  # Empty files handled elsewhere
        if not any(content.startswith(sig) for sig in XLSX_MAGIC_BYTES):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File content does not appear to be valid XLSX format.",
            )
        return True
    return True


def _sanitize_filename(filename: str | None) -> str:
    """
    Sanitize a filename to prevent path traversal and remove special characters.

    Args:
        filename: The original filename (may be None)

    Returns:
        Sanitized filename, or "unknown" if result is empty
    """
    if not filename:
        return "unknown"

    # Strip path separators using os.path.basename
    name = os.path.basename(filename)

    # Remove special characters, keep alphanumeric, dash, underscore, dot
    name = re.sub(r"[^a-zA-Z0-9._-]", "", name)

    # Return "unknown" if result is empty
    return name if name else "unknown"


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
    # Validate content type (handle charset variations like "text/csv; charset=utf-8")
    base_content_type = (file.content_type or "").split(";")[0].strip()
    if base_content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file.content_type}. Only CSV and XLSX files are accepted.",
        )

    # Read file content
    content = await file.read()

    # Validate file is not empty
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty. Please upload a file with content.",
        )

    # Validate file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024 * 1024)}MB.",
        )

    # Validate file content matches claimed type (magic byte validation)
    _validate_file_content(content, base_content_type)

    # Sanitize filename
    safe_filename = _sanitize_filename(file.filename)

    # Process the upload
    result = await service.process_upload(
        session_id=session_id,
        file_name=safe_filename,
        content=content,
    )

    # Extract column names from detected_schema dict
    # schema_data has format: {"columns": [{"name": "col1", ...}, ...], "dtypes": {...}}
    schema_data = result["detected_schema"]
    if isinstance(schema_data, dict):
        raw_columns = schema_data.get("columns", [])
        # Columns may be list of dicts with "name" key, or list of strings
        column_names = [
            col["name"] if isinstance(col, dict) else col
            for col in raw_columns
        ]
    else:
        column_names = schema_data

    # Auto-detect column mappings
    column_detector = ColumnDetectionService()
    detected = column_detector.detect_mappings_sync(
        columns=column_names,
        sample_rows=result.get("preview", []),
    )

    return UploadResponse(
        id=UUID(result["id"]),
        file_name=result["file_name"],
        row_count=result["row_count"],
        detected_schema=column_names,
        created_at=datetime.fromisoformat(result["created_at"]),
        column_mappings=result.get("column_mappings"),
        detected_mappings=[
            DetectedMappingResponse(
                field=m.field,
                column=m.column,
                confidence=m.confidence,
                alternatives=m.alternatives,
                required=m.required,
            )
            for m in detected
        ],
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

    uploads = []
    for item in results:
        schema_data = item["detected_schema"]
        if isinstance(schema_data, dict):
            raw_columns = schema_data.get("columns", [])
            column_names = [
                col["name"] if isinstance(col, dict) else col
                for col in raw_columns
            ]
        else:
            column_names = schema_data
        uploads.append(
            UploadResponse(
                id=UUID(item["id"]),
                file_name=item["file_name"],
                row_count=item["row_count"],
                detected_schema=column_names,
                created_at=datetime.fromisoformat(item["created_at"]),
                column_mappings=item.get("column_mappings"),
            )
        )
    return uploads


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

    schema_data = result["detected_schema"]
    if isinstance(schema_data, dict):
        raw_columns = schema_data.get("columns", [])
        column_names = [
            col["name"] if isinstance(col, dict) else col
            for col in raw_columns
        ]
    else:
        column_names = schema_data

    return UploadResponse(
        id=UUID(result["id"]),
        file_name=result["file_name"],
        row_count=result["row_count"],
        detected_schema=column_names,
        created_at=datetime.fromisoformat(result["created_at"]),
        column_mappings=result.get("column_mappings"),
    )
