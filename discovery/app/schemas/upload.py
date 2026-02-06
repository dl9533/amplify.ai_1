"""Upload schemas for the Discovery module."""
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DetectedMappingResponse(BaseModel):
    """Column detection result for a field."""

    field: str = Field(
        ...,
        description="Field type (role, lob, department, geography)",
    )
    column: Optional[str] = Field(
        default=None,
        description="Detected column name, or null if not detected",
    )
    confidence: float = Field(
        ...,
        ge=0,
        le=1,
        description="Confidence score (0-1)",
    )
    alternatives: List[str] = Field(
        default_factory=list,
        description="Alternative column choices",
    )
    required: bool = Field(
        ...,
        description="Whether this field is required",
    )


class UploadResponse(BaseModel):
    """Schema for upload response."""

    id: UUID = Field(
        ...,
        description="Unique upload identifier",
    )
    file_name: str = Field(
        ...,
        description="Name of the uploaded file",
    )
    row_count: int = Field(
        ...,
        description="Number of data rows in the file",
    )
    detected_schema: List[str] = Field(
        ...,
        description="List of column names detected in the file",
    )
    created_at: datetime = Field(
        ...,
        description="When the upload was created",
    )
    column_mappings: Optional[Dict[str, str]] = Field(
        default=None,
        description="Column mappings for role, department, geography",
    )
    detected_mappings: Optional[List[DetectedMappingResponse]] = Field(
        default=None,
        description="Auto-detected column mappings with confidence scores",
    )

    model_config = {
        "from_attributes": True,
    }


class ColumnMappingUpdate(BaseModel):
    """Schema for updating column mappings."""

    role: Optional[str] = Field(
        default=None,
        description="Column name to map as role",
    )
    lob: Optional[str] = Field(
        default=None,
        description="Column name to map as line of business",
    )
    department: Optional[str] = Field(
        default=None,
        description="Column name to map as department",
    )
    geography: Optional[str] = Field(
        default=None,
        description="Column name to map as geography",
    )
    headcount: Optional[str] = Field(
        default=None,
        description="Column name to map as employee headcount (will be summed per role)",
    )
