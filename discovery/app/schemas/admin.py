"""Admin schemas for the Discovery module."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class OnetSyncRequest(BaseModel):
    """Request to sync O*NET database."""

    version: str = Field(
        default="30_1",
        description="O*NET version to sync (e.g., '30_1' for v30.1)",
        pattern=r"^\d+_\d+$",
    )


class OnetSyncResponse(BaseModel):
    """Response from O*NET sync operation."""

    version: str = Field(
        ...,
        description="O*NET version that was synced",
    )
    occupation_count: int = Field(
        ...,
        ge=0,
        description="Number of occupations imported",
    )
    alternate_title_count: int = Field(
        ...,
        ge=0,
        description="Number of alternate titles imported",
    )
    task_count: int = Field(
        ...,
        ge=0,
        description="Number of tasks imported",
    )
    status: str = Field(
        ...,
        description="Sync status (success or failed)",
    )


class OnetSyncStatus(BaseModel):
    """Current O*NET sync status."""

    synced: bool = Field(
        ...,
        description="Whether O*NET data has been synced",
    )
    version: Optional[str] = Field(
        default=None,
        description="Current O*NET version (if synced)",
    )
    synced_at: Optional[datetime] = Field(
        default=None,
        description="When the last sync occurred",
    )
    occupation_count: int = Field(
        ...,
        ge=0,
        description="Number of occupations in database",
    )
