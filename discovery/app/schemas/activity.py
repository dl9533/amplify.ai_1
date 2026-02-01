"""Activity schemas for the Discovery module."""
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DWAResponse(BaseModel):
    """Schema for Detailed Work Activity (DWA) response."""

    id: UUID = Field(
        ...,
        description="Unique DWA identifier",
    )
    code: str = Field(
        ...,
        description="DWA code (e.g., 4.A.1.a.1)",
    )
    title: str = Field(
        ...,
        description="DWA title",
    )
    description: Optional[str] = Field(
        default=None,
        description="DWA description",
    )
    selected: bool = Field(
        ...,
        description="Whether the DWA is selected",
    )
    gwa_code: str = Field(
        ...,
        description="Parent GWA code",
    )

    model_config = {
        "from_attributes": True,
    }


class GWAGroupResponse(BaseModel):
    """Schema for Generalized Work Activity (GWA) group response."""

    gwa_code: str = Field(
        ...,
        description="GWA code (e.g., 4.A.1)",
    )
    gwa_title: str = Field(
        ...,
        description="GWA title",
    )
    dwas: list[DWAResponse] = Field(
        ...,
        description="List of DWAs in this GWA group",
    )

    model_config = {
        "from_attributes": True,
    }


class ActivitySelectionUpdate(BaseModel):
    """Schema for updating activity selection status."""

    selected: bool = Field(
        ...,
        description="Selection status to set",
    )


class BulkSelectionRequest(BaseModel):
    """Schema for bulk selection request."""

    activity_ids: list[UUID] = Field(
        ...,
        description="List of activity IDs to update",
    )
    selected: bool = Field(
        ...,
        description="Selection status to set for all activities",
    )


class BulkSelectionResponse(BaseModel):
    """Schema for bulk selection response."""

    updated_count: int = Field(
        ...,
        ge=0,
        description="Number of activities updated",
    )


class SelectionCountResponse(BaseModel):
    """Schema for selection count statistics."""

    total: int = Field(
        ...,
        ge=0,
        description="Total number of activities",
    )
    selected: int = Field(
        ...,
        ge=0,
        description="Number of selected activities",
    )
    unselected: int = Field(
        ...,
        ge=0,
        description="Number of unselected activities",
    )
