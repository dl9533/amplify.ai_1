"""Session schemas for the Discovery module."""
from datetime import datetime
from enum import Enum
from typing import List
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.data import VALID_NAICS_SECTORS


def _validate_naics_sector(v: str | None) -> str | None:
    """Validate that a NAICS sector code is in the valid list."""
    if v is not None and v not in VALID_NAICS_SECTORS:
        raise ValueError(
            f"Invalid NAICS sector code: {v}. "
            f"Must be one of: {', '.join(sorted(VALID_NAICS_SECTORS))}"
        )
    return v


class SessionStatus(str, Enum):
    """Enum for session status values."""

    PENDING = "pending"
    UPLOAD_COMPLETE = "upload_complete"
    MAPPING_COMPLETE = "mapping_complete"
    ANALYSIS_COMPLETE = "analysis_complete"
    FINALIZED = "finalized"


class SessionCreate(BaseModel):
    """Schema for creating a new discovery session."""

    organization_id: UUID = Field(
        ...,
        description="The organization ID for the session",
    )
    industry_naics_sector: str | None = Field(
        default=None,
        min_length=2,
        max_length=2,
        pattern=r"^\d{2}$",
        description="2-digit NAICS sector code for the company's industry",
    )

    @field_validator("industry_naics_sector")
    @classmethod
    def validate_naics_sector(cls, v: str | None) -> str | None:
        """Validate NAICS sector code against known values."""
        return _validate_naics_sector(v)


class SessionResponse(BaseModel):
    """Schema for session response."""

    id: UUID = Field(
        ...,
        description="Unique session identifier",
    )
    status: SessionStatus = Field(
        ...,
        description="Current session status (draft, in_progress, completed)",
    )
    current_step: int = Field(
        ...,
        description="Current step number in the discovery workflow",
    )
    industry_naics_sector: str | None = Field(
        default=None,
        description="2-digit NAICS sector code for the company's industry",
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


class IndustryUpdate(BaseModel):
    """Schema for updating session industry."""

    industry_naics_sector: str | None = Field(
        default=None,
        min_length=2,
        max_length=2,
        pattern=r"^\d{2}$",
        description="2-digit NAICS sector code for the company's industry (null to clear)",
    )

    @field_validator("industry_naics_sector")
    @classmethod
    def validate_naics_sector(cls, v: str | None) -> str | None:
        """Validate NAICS sector code against known values."""
        return _validate_naics_sector(v)
