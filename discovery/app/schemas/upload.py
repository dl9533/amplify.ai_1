"""Upload schemas for the Discovery module."""
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


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

    model_config = {
        "from_attributes": True,
    }


class ColumnMappingUpdate(BaseModel):
    """Schema for updating column mappings."""

    role: Optional[str] = Field(
        default=None,
        description="Column name to map as role",
    )
    department: Optional[str] = Field(
        default=None,
        description="Column name to map as department",
    )
    geography: Optional[str] = Field(
        default=None,
        description="Column name to map as geography",
    )
