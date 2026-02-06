"""Industry schemas for the Discovery module."""
from pydantic import BaseModel, Field


class NaicsSectorResponse(BaseModel):
    """Schema for a NAICS sector."""

    code: str = Field(
        ...,
        description="2-digit NAICS sector code",
        examples=["52"],
    )
    label: str = Field(
        ...,
        description="Human-readable sector name",
        examples=["Finance & Insurance"],
    )


class SupersectorResponse(BaseModel):
    """Schema for a BLS supersector with its NAICS sectors."""

    code: str = Field(
        ...,
        description="Supersector code identifier",
        examples=["FINANCIAL_ACTIVITIES"],
    )
    label: str = Field(
        ...,
        description="Human-readable supersector name",
        examples=["Financial Activities"],
    )
    sectors: list[NaicsSectorResponse] = Field(
        ...,
        description="List of NAICS sectors in this supersector",
    )


class IndustryListResponse(BaseModel):
    """Schema for the full industry list response."""

    supersectors: list[SupersectorResponse] = Field(
        ...,
        description="List of all BLS supersectors with their NAICS sectors",
    )
