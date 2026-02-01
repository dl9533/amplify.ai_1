"""Handoff schemas for the Discovery module."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class HandoffRequest(BaseModel):
    """Schema for handoff submission request.

    Either candidate_ids or priority_tier should be provided
    to specify which candidates to hand off.
    """

    candidate_ids: Optional[list[UUID]] = Field(
        None,
        description="List of candidate IDs to hand off to intake",
    )
    notes: Optional[str] = Field(
        None,
        description="Optional notes to include with the handoff",
    )
    priority_tier: Optional[str] = Field(
        None,
        description="Priority tier filter (HIGH, MEDIUM, LOW)",
    )

    model_config = {
        "from_attributes": True,
    }


class HandoffResponse(BaseModel):
    """Schema for handoff submission response."""

    intake_request_id: UUID = Field(
        ...,
        description="ID of the created intake request",
    )
    status: str = Field(
        ...,
        description="Status of the handoff submission (e.g., 'submitted')",
    )
    candidates_count: int = Field(
        ...,
        description="Number of candidates included in the handoff",
    )

    model_config = {
        "from_attributes": True,
    }


class ValidationResult(BaseModel):
    """Schema for handoff validation result."""

    is_ready: bool = Field(
        ...,
        description="Whether the session is ready for handoff",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Non-blocking warnings about the handoff",
    )
    errors: list[str] = Field(
        default_factory=list,
        description="Blocking errors that prevent handoff",
    )

    model_config = {
        "from_attributes": True,
    }


class HandoffStatus(BaseModel):
    """Schema for handoff status response."""

    session_id: UUID = Field(
        ...,
        description="ID of the discovery session",
    )
    handed_off: bool = Field(
        ...,
        description="Whether the session has been handed off",
    )
    intake_request_id: Optional[UUID] = Field(
        None,
        description="ID of the intake request if handed off",
    )
    handed_off_at: Optional[datetime] = Field(
        None,
        description="Timestamp of when the handoff occurred",
    )

    model_config = {
        "from_attributes": True,
    }


class HandoffError(BaseModel):
    """Schema for handoff error response."""

    detail: str = Field(
        ...,
        description="Human-readable error message",
    )
    errors: list[str] = Field(
        ...,
        description="List of specific error messages",
    )

    model_config = {
        "from_attributes": True,
    }
