"""LOB mapping schemas for the Discovery module."""
from typing import List

from pydantic import BaseModel, Field


class LobNaicsLookupResponse(BaseModel):
    """Response for LOB to NAICS lookup."""

    lob: str = Field(
        ...,
        description="Line of Business that was looked up",
    )
    naics_codes: List[str] = Field(
        ...,
        description="NAICS industry codes for the LOB",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score of the mapping (0-1)",
    )
    source: str = Field(
        ...,
        description="Source of the mapping: 'curated', 'fuzzy', or 'llm'",
    )
