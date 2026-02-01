"""Session schemas for the Discovery module."""
from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class SessionCreate(BaseModel):
    """Schema for creating a new discovery session."""

    organization_id: UUID = Field(
        ...,
        description="The organization ID for the session",
    )


class SessionResponse(BaseModel):
    """Schema for session response."""

    id: UUID = Field(
        ...,
        description="Unique session identifier",
    )
    status: str = Field(
        ...,
        description="Current session status (draft, in_progress, completed)",
    )
    current_step: int = Field(
        ...,
        description="Current step number in the discovery workflow",
    )
    created_at: datetime = Field(
        ...,
        description="When the session was created",
    )
    updated_at: datetime = Field(
        ...,
        description="When the session was last updated",
    )

    model_config = {
        "from_attributes": True,
    }


class SessionList(BaseModel):
    """Schema for paginated session list."""

    items: List[SessionResponse] = Field(
        ...,
        description="List of sessions",
    )
    total: int = Field(
        ...,
        description="Total number of sessions",
    )
    page: int = Field(
        ...,
        description="Current page number",
    )
    per_page: int = Field(
        ...,
        description="Number of items per page",
    )


class StepUpdate(BaseModel):
    """Schema for updating session step."""

    step: int = Field(
        ...,
        gt=0,
        description="The new step number (must be positive)",
    )

    @field_validator("step")
    @classmethod
    def validate_step_positive(cls, v: int) -> int:
        """Validate that step is a positive integer."""
        if v <= 0:
            raise ValueError("Step must be a positive integer")
        return v
