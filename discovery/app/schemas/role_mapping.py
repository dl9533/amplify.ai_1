"""Role mapping schemas for the Discovery module."""
import re
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

# O*NET code format: XX-XXXX.XX (e.g., 15-1252.00)
ONET_CODE_PATTERN = re.compile(r"^\d{2}-\d{4}\.\d{2}$")


def validate_onet_code(code: str) -> str:
    """Validate O*NET code format (XX-XXXX.XX)."""
    if not ONET_CODE_PATTERN.match(code):
        raise ValueError(
            f"Invalid O*NET code format: {code}. Expected format: XX-XXXX.XX (e.g., 15-1252.00)"
        )
    return code


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
    onet_code: Optional[str] = Field(
        default=None,
        description="O*NET SOC code for the mapped occupation",
    )
    onet_title: Optional[str] = Field(
        default=None,
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

    @field_validator("onet_code")
    @classmethod
    def validate_onet_code_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate O*NET code format if provided."""
        if v is not None:
            return validate_onet_code(v)
        return v

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

    @field_validator("onet_code")
    @classmethod
    def validate_onet_code_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate O*NET code format if provided."""
        if v is not None:
            return validate_onet_code(v)
        return v


class BulkConfirmRequest(BaseModel):
    """Schema for bulk confirm request."""

    threshold: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Minimum confidence score threshold for auto-confirmation (0-1)",
    )


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
