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
        default=0.85,
        ge=0.0,
        le=1.0,
        description="Minimum confidence score threshold for auto-confirmation (0-1). Defaults to 0.85.",
    )
    lob: Optional[str] = Field(
        default=None,
        description="Optional Line of Business filter to confirm only mappings in this LOB",
    )
    mapping_ids: Optional[List[UUID]] = Field(
        default=None,
        description="Optional specific mapping IDs to confirm. If provided, only these mappings are considered.",
    )


class BulkConfirmResponse(BaseModel):
    """Schema for bulk confirm response."""

    confirmed_count: int = Field(
        ...,
        ge=0,
        description="Number of mappings confirmed",
    )


class BulkRemapRequest(BaseModel):
    """Schema for bulk remap request."""

    threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Maximum confidence score threshold for re-mapping (0-1). Roles at or below this will be re-mapped.",
    )
    mapping_ids: Optional[List[UUID]] = Field(
        default=None,
        description="Specific mapping IDs to re-map. If None, all mappings below threshold are re-mapped.",
    )


class BulkRemapResponse(BaseModel):
    """Schema for bulk remap response."""

    remapped_count: int = Field(
        ...,
        ge=0,
        description="Number of mappings re-mapped",
    )
    mappings: List["RoleMappingWithReasoning"] = Field(
        default_factory=list,
        description="Updated mapping results with new confidence scores",
    )


class RoleMappingWithReasoning(BaseModel):
    """Role mapping response with LLM reasoning."""

    id: UUID = Field(..., description="Unique role mapping identifier")
    source_role: str = Field(..., description="Original role title")
    onet_code: Optional[str] = Field(default=None, description="O*NET SOC code")
    onet_title: Optional[str] = Field(default=None, description="O*NET occupation title")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    confidence_tier: str = Field(..., description="Confidence tier: HIGH, MEDIUM, or LOW")
    reasoning: Optional[str] = Field(default=None, description="LLM reasoning for the mapping")
    is_confirmed: bool = Field(..., description="Whether confirmed by user")


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


class GroupedMappingSummary(BaseModel):
    """Summary statistics for a group of role mappings."""

    total_roles: int = Field(
        ...,
        ge=0,
        description="Total number of unique roles in the group",
    )
    confirmed_count: int = Field(
        ...,
        ge=0,
        description="Number of confirmed mappings",
    )
    pending_count: int = Field(
        ...,
        ge=0,
        description="Number of pending (unconfirmed) mappings",
    )
    low_confidence_count: int = Field(
        ...,
        ge=0,
        description="Number of low confidence mappings (below 0.6)",
    )
    total_employees: int = Field(
        ...,
        ge=0,
        description="Total employee count across all roles in the group",
    )


class RoleMappingCompact(BaseModel):
    """Compact role mapping for grouped display."""

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
    employee_count: int = Field(
        ...,
        ge=0,
        description="Number of employees with this role",
    )

    model_config = {
        "from_attributes": True,
    }


class LobGroup(BaseModel):
    """Group of role mappings by Line of Business."""

    lob: str = Field(
        ...,
        description="Line of Business name",
    )
    summary: GroupedMappingSummary = Field(
        ...,
        description="Summary statistics for this LOB group",
    )
    mappings: List[RoleMappingCompact] = Field(
        default_factory=list,
        description="Role mappings in this LOB group",
    )


class GroupedRoleMappingsResponse(BaseModel):
    """Response for grouped role mappings endpoint."""

    session_id: UUID = Field(
        ...,
        description="Discovery session ID",
    )
    overall_summary: GroupedMappingSummary = Field(
        ...,
        description="Summary statistics across all groups",
    )
    lob_groups: List[LobGroup] = Field(
        default_factory=list,
        description="Role mappings grouped by Line of Business",
    )
    ungrouped_mappings: List[RoleMappingCompact] = Field(
        default_factory=list,
        description="Role mappings without LOB assignment",
    )


class CreateMappingsRequest(BaseModel):
    """Schema for create mappings request."""

    upload_id: UUID = Field(
        ...,
        description="ID of the upload containing workforce data",
    )


class CreateMappingsResponse(BaseModel):
    """Schema for create mappings response."""

    created_count: int = Field(
        ...,
        ge=0,
        description="Number of role mappings created",
    )
    mappings: List[RoleMappingWithReasoning] = Field(
        default_factory=list,
        description="Created role mappings with LLM reasoning",
    )
