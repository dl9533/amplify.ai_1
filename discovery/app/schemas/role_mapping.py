"""Role mapping schemas for the Discovery module."""
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class RoleMappingResponse(BaseModel):
    """Schema for role mapping response."""

    id: UUID = Field(
        ...,
        description="Unique role mapping identifier",
    )
    source_role: str = Field(
        ...,
        description="Original role title from uploaded data",
    )
    onet_code: str = Field(
        ...,
        description="O*NET SOC code for the mapped occupation",
    )
    onet_title: str = Field(
        ...,
        description="O*NET occupation title",
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score of the mapping (0-1)",
    )
    is_confirmed: bool = Field(
        ...,
        description="Whether the mapping has been confirmed by user",
    )

    model_config = {
        "from_attributes": True,
    }


class RoleMappingUpdate(BaseModel):
    """Schema for updating a role mapping."""

    onet_code: Optional[str] = Field(
        default=None,
        description="O*NET SOC code for the mapped occupation",
    )
    onet_title: Optional[str] = Field(
        default=None,
        description="O*NET occupation title",
    )
    is_confirmed: Optional[bool] = Field(
        default=None,
        description="Whether the mapping has been confirmed by user",
    )


class BulkConfirmRequest(BaseModel):
    """Schema for bulk confirm request."""

    threshold: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Minimum confidence score threshold for auto-confirmation (0-1)",
    )

    @field_validator("threshold")
    @classmethod
    def validate_threshold(cls, v: float) -> float:
        """Validate threshold is between 0 and 1."""
        if v < 0.0 or v > 1.0:
            raise ValueError("Threshold must be between 0 and 1")
        return v


class BulkConfirmResponse(BaseModel):
    """Schema for bulk confirm response."""

    confirmed_count: int = Field(
        ...,
        ge=0,
        description="Number of mappings confirmed",
    )


class OnetSearchResult(BaseModel):
    """Schema for O*NET search result."""

    code: str = Field(
        ...,
        description="O*NET SOC code",
    )
    title: str = Field(
        ...,
        description="O*NET occupation title",
    )
    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Search relevance score (0-1)",
    )


class OnetOccupation(BaseModel):
    """Schema for O*NET occupation details."""

    code: str = Field(
        ...,
        description="O*NET SOC code",
    )
    title: str = Field(
        ...,
        description="O*NET occupation title",
    )
    description: Optional[str] = Field(
        default=None,
        description="O*NET occupation description",
    )
    gwas: Optional[List[Any]] = Field(
        default=None,
        description="Generalized Work Activities associated with the occupation",
    )

    model_config = {
        "from_attributes": True,
    }
