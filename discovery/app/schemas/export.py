"""Export schemas for the Discovery module."""
from typing import Any

from pydantic import BaseModel, Field


class HandoffBundle(BaseModel):
    """Schema for the handoff export bundle.

    Contains all data needed to hand off discovery results
    to downstream systems or processes.
    """

    session_summary: dict[str, Any] = Field(
        ...,
        description="Summary information about the discovery session",
    )
    role_mappings: list[dict[str, Any]] = Field(
        ...,
        description="List of role mappings with O*NET codes and activities",
    )
    analysis_results: list[dict[str, Any]] = Field(
        ...,
        description="Analysis results across all dimensions",
    )
    roadmap: list[dict[str, Any]] = Field(
        ...,
        description="Implementation roadmap with phases and items",
    )

    model_config = {
        "from_attributes": True,
    }
