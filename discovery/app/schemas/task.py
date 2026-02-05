"""Task schemas for the Discovery module."""
from uuid import UUID

from pydantic import BaseModel, Field


class TaskResponse(BaseModel):
    """Schema for Task response."""

    id: UUID = Field(
        ...,
        description="Unique selection identifier",
    )
    role_mapping_id: UUID = Field(
        ...,
        description="Role mapping identifier this task belongs to",
    )
    task_id: int = Field(
        ...,
        description="O*NET task ID",
    )
    description: str | None = Field(
        default=None,
        description="Task description",
    )
    importance: float | None = Field(
        default=None,
        description="Task importance score from O*NET",
    )
    selected: bool = Field(
        ...,
        description="Whether the task is selected",
    )
    user_modified: bool = Field(
        default=False,
        description="Whether user has modified the selection",
    )

    model_config = {
        "from_attributes": True,
    }


class TaskSelectionUpdate(BaseModel):
    """Schema for updating task selection status."""

    selected: bool = Field(
        ...,
        description="Selection status to set",
    )


class TaskBulkUpdateRequest(BaseModel):
    """Schema for bulk task selection update request."""

    task_ids: list[int] = Field(
        ...,
        min_length=1,
        description="List of O*NET task IDs to update (must have at least one)",
    )
    selected: bool = Field(
        ...,
        description="Selection status to set for all tasks",
    )


class TaskBulkUpdateResponse(BaseModel):
    """Schema for bulk task selection update response."""

    updated_count: int = Field(
        ...,
        ge=0,
        description="Number of tasks updated",
    )


class TaskSelectionStatsResponse(BaseModel):
    """Schema for task selection statistics."""

    total: int = Field(
        ...,
        ge=0,
        description="Total number of tasks",
    )
    selected: int = Field(
        ...,
        ge=0,
        description="Number of selected tasks",
    )
    unselected: int = Field(
        ...,
        ge=0,
        description="Number of unselected tasks",
    )


class TaskLoadResponse(BaseModel):
    """Schema for task load operation response."""

    mappings_processed: int = Field(
        ...,
        ge=0,
        description="Number of role mappings processed",
    )
    tasks_loaded: int = Field(
        ...,
        ge=0,
        description="Total number of tasks loaded",
    )


class RoleMappingTasksResponse(BaseModel):
    """Schema for tasks grouped by role mapping."""

    role_mapping_id: UUID = Field(
        ...,
        description="Role mapping identifier",
    )
    source_role: str = Field(
        ...,
        description="Original role name from upload",
    )
    onet_code: str | None = Field(
        default=None,
        description="O*NET occupation code",
    )
    onet_title: str | None = Field(
        default=None,
        description="O*NET occupation title",
    )
    tasks: list[TaskResponse] = Field(
        default_factory=list,
        description="Tasks for this role mapping",
    )

    model_config = {
        "from_attributes": True,
    }


class TaskWithDWAsResponse(BaseModel):
    """Schema for task with associated DWAs for AI analysis."""

    task_id: int = Field(
        ...,
        description="O*NET task ID",
    )
    description: str = Field(
        ...,
        description="Task description",
    )
    importance: float | None = Field(
        default=None,
        description="Task importance score",
    )
    dwa_ids: list[str] = Field(
        default_factory=list,
        description="List of associated DWA IDs",
    )

    model_config = {
        "from_attributes": True,
    }
