"""Analysis schemas for the Discovery module."""
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, RootModel


class AnalysisDimension(str, Enum):
    """Enumeration of analysis dimensions."""

    ROLE = "role"
    DEPARTMENT = "department"
    LOB = "lob"
    GEOGRAPHY = "geography"
    TASK = "task"


class PriorityTier(str, Enum):
    """Enumeration of priority tiers for analysis results."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class AnalysisResult(BaseModel):
    """Schema for individual analysis result."""

    id: UUID = Field(
        ...,
        description="Unique identifier for the analyzed entity",
    )
    name: str = Field(
        ...,
        description="Name of the analyzed entity",
    )
    ai_exposure_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="AI exposure score (0.0-1.0)",
    )
    impact_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Impact score (0.0-1.0)",
    )
    complexity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Complexity score (0.0-1.0)",
    )
    priority_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Priority score (0.0-1.0)",
    )
    priority_tier: PriorityTier = Field(
        ...,
        description="Priority tier classification",
    )
    row_count: int | None = Field(
        default=None,
        ge=0,
        description="Number of employees/rows for this entity",
    )

    model_config = {
        "from_attributes": True,
    }


class DimensionAnalysisResponse(BaseModel):
    """Schema for analysis results by dimension."""

    dimension: AnalysisDimension = Field(
        ...,
        description="The analysis dimension",
    )
    results: list[AnalysisResult] = Field(
        ...,
        description="List of analysis results for the dimension",
    )

    model_config = {
        "from_attributes": True,
    }


class DimensionSummary(BaseModel):
    """Schema for dimension summary statistics."""

    count: int = Field(
        ...,
        ge=0,
        description="Number of entities in the dimension",
    )
    avg_exposure: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Average AI exposure score for the dimension (0.0-1.0)",
    )

    model_config = {
        "from_attributes": True,
    }


class AllDimensionsResponse(RootModel[dict[str, DimensionSummary]]):
    """Schema for all dimensions summary response.

    Returns a dictionary with dimension names as keys and DimensionSummary as values.
    Example: {"ROLE": {"count": 15, "avg_exposure": 0.68}, ...}
    """

    pass


class TriggerAnalysisResponse(BaseModel):
    """Schema for trigger analysis response."""

    status: str = Field(
        ...,
        description="Status of the analysis request",
    )

    model_config = {
        "from_attributes": True,
    }
