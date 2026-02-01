"""Roadmap schemas for the Discovery module."""
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class RoadmapPhase(str, Enum):
    """Enumeration of roadmap phases for prioritization."""

    NOW = "NOW"
    NEXT = "NEXT"
    LATER = "LATER"


class EstimatedEffort(str, Enum):
    """Enumeration of estimated effort levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RoadmapItem(BaseModel):
    """Schema for a single roadmap item."""

    id: UUID = Field(
        ...,
        description="Unique identifier for the roadmap item",
    )
    role_name: str = Field(
        ...,
        description="Name of the role being prioritized",
    )
    priority_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Priority score (0.0-1.0)",
    )
    priority_tier: str = Field(
        ...,
        description="Priority tier classification (HIGH, MEDIUM, LOW)",
    )
    phase: RoadmapPhase = Field(
        ...,
        description="Current roadmap phase",
    )
    estimated_effort: EstimatedEffort = Field(
        ...,
        description="Estimated effort level",
    )
    order: Optional[int] = Field(
        default=None,
        description="Display order within the phase",
    )

    model_config = {
        "from_attributes": True,
    }


class RoadmapItemsResponse(BaseModel):
    """Schema for list of roadmap items."""

    items: list[RoadmapItem] = Field(
        ...,
        description="List of roadmap items",
    )

    model_config = {
        "from_attributes": True,
    }


class PhaseUpdate(BaseModel):
    """Schema for updating a roadmap item's phase."""

    phase: RoadmapPhase = Field(
        ...,
        description="New phase for the roadmap item",
    )

    model_config = {
        "from_attributes": True,
    }


class ReorderRequest(BaseModel):
    """Schema for reordering roadmap items."""

    item_ids: list[UUID] = Field(
        ...,
        description="Ordered list of roadmap item IDs",
    )

    model_config = {
        "from_attributes": True,
    }


class ReorderResponse(BaseModel):
    """Schema for reorder response."""

    success: bool = Field(
        ...,
        description="Whether the reorder operation succeeded",
    )

    model_config = {
        "from_attributes": True,
    }


class BulkPhaseUpdate(BaseModel):
    """Schema for a single bulk phase update item."""

    id: UUID = Field(
        ...,
        description="ID of the roadmap item to update",
    )
    phase: RoadmapPhase = Field(
        ...,
        description="New phase for the item",
    )

    model_config = {
        "from_attributes": True,
    }


class BulkUpdateRequest(BaseModel):
    """Schema for bulk phase update request."""

    updates: list[BulkPhaseUpdate] = Field(
        ...,
        description="List of phase updates to apply",
    )

    model_config = {
        "from_attributes": True,
    }


class BulkUpdateResponse(BaseModel):
    """Schema for bulk update response."""

    updated_count: int = Field(
        ...,
        ge=0,
        description="Number of items successfully updated",
    )

    model_config = {
        "from_attributes": True,
    }
