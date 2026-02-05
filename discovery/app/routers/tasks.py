"""Tasks router for the Discovery module."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.schemas.task import (
    RoleMappingTasksResponse,
    TaskBulkUpdateRequest,
    TaskBulkUpdateResponse,
    TaskLoadResponse,
    TaskResponse,
    TaskSelectionStatsResponse,
    TaskSelectionUpdate,
    TaskWithDWAsResponse,
)
from app.services.task_service import (
    TaskService,
    get_task_service,
)

router = APIRouter(
    prefix="/discovery",
    tags=["discovery-tasks"],
)


@router.get(
    "/sessions/{session_id}/tasks",
    response_model=list[TaskResponse],
    status_code=status.HTTP_200_OK,
    summary="Get tasks for session",
    description="Retrieves all task selections for a specific discovery session.",
)
async def get_tasks_for_session(
    session_id: UUID,
    include_unselected: bool = Query(
        default=True,
        description="Whether to include unselected tasks",
    ),
    service: TaskService = Depends(get_task_service),
) -> list[TaskResponse]:
    """Get all tasks for a session."""
    results = await service.get_tasks_for_session(
        session_id=session_id,
        include_unselected=include_unselected,
    )

    return [
        TaskResponse(
            id=UUID(r["id"]),
            role_mapping_id=UUID(r["role_mapping_id"]),
            task_id=r["task_id"],
            description=r.get("description"),
            importance=r.get("importance"),
            selected=r["selected"],
            user_modified=r["user_modified"],
        )
        for r in results
    ]


@router.get(
    "/role-mappings/{role_mapping_id}/tasks",
    response_model=list[TaskResponse],
    status_code=status.HTTP_200_OK,
    summary="Get tasks for role mapping",
    description="Retrieves task selections for a specific role mapping.",
)
async def get_tasks_for_role_mapping(
    role_mapping_id: UUID,
    service: TaskService = Depends(get_task_service),
) -> list[TaskResponse]:
    """Get tasks for a specific role mapping."""
    results = await service.get_tasks_for_role_mapping(
        role_mapping_id=role_mapping_id,
    )

    return [
        TaskResponse(
            id=UUID(r["id"]),
            role_mapping_id=UUID(r["role_mapping_id"]),
            task_id=r["task_id"],
            description=r.get("description"),
            importance=r.get("importance"),
            selected=r["selected"],
            user_modified=r["user_modified"],
        )
        for r in results
    ]


@router.get(
    "/sessions/{session_id}/tasks/grouped",
    response_model=list[RoleMappingTasksResponse],
    status_code=status.HTTP_200_OK,
    summary="Get tasks grouped by role mapping",
    description="Retrieves all tasks for a session grouped by role mapping. "
    "This endpoint is optimized for frontend loading to avoid N+1 queries.",
)
async def get_tasks_grouped_by_mapping(
    session_id: UUID,
    service: TaskService = Depends(get_task_service),
) -> list[RoleMappingTasksResponse]:
    """Get all tasks grouped by role mapping for efficient frontend loading."""
    results = await service.get_tasks_grouped_by_mapping(session_id=session_id)

    return [
        RoleMappingTasksResponse(
            role_mapping_id=UUID(r["role_mapping_id"]),
            source_role=r["source_role"],
            onet_code=r.get("onet_code"),
            onet_title=r.get("onet_title"),
            tasks=[
                TaskResponse(
                    id=UUID(t["id"]),
                    role_mapping_id=UUID(t["role_mapping_id"]),
                    task_id=t["task_id"],
                    description=t.get("description"),
                    importance=t.get("importance"),
                    selected=t["selected"],
                    user_modified=t["user_modified"],
                )
                for t in r["tasks"]
            ],
        )
        for r in results
    ]


@router.put(
    "/tasks/{selection_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Update task selection",
    description="Updates the selection status of a single task.",
)
async def update_task_selection(
    selection_id: UUID,
    update_data: TaskSelectionUpdate,
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    """Update the selection status of a task."""
    result = await service.update_selection(
        selection_id=selection_id,
        selected=update_data.selected,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task selection with ID {selection_id} not found",
        )

    return TaskResponse(
        id=UUID(result["id"]),
        role_mapping_id=UUID(result["role_mapping_id"]),
        task_id=result["task_id"],
        description=result.get("description"),
        importance=result.get("importance"),
        selected=result["selected"],
        user_modified=result["user_modified"],
    )


@router.post(
    "/role-mappings/{role_mapping_id}/tasks/bulk-update",
    response_model=TaskBulkUpdateResponse,
    status_code=status.HTTP_200_OK,
    summary="Bulk update task selections",
    description="Bulk update selection status for multiple tasks in a role mapping.",
)
async def bulk_update_tasks(
    role_mapping_id: UUID,
    request: TaskBulkUpdateRequest,
    service: TaskService = Depends(get_task_service),
) -> TaskBulkUpdateResponse:
    """Bulk update task selections."""
    result = await service.bulk_update_selections(
        role_mapping_id=role_mapping_id,
        task_ids=request.task_ids,
        selected=request.selected,
    )

    return TaskBulkUpdateResponse(updated_count=result["updated_count"])


@router.get(
    "/sessions/{session_id}/tasks/stats",
    response_model=TaskSelectionStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get task selection statistics",
    description="Get task selection count statistics for a session.",
)
async def get_task_selection_stats(
    session_id: UUID,
    service: TaskService = Depends(get_task_service),
) -> TaskSelectionStatsResponse:
    """Get task selection statistics for a session."""
    result = await service.get_selection_stats(session_id=session_id)

    return TaskSelectionStatsResponse(
        total=result["total"],
        selected=result["selected"],
        unselected=result["unselected"],
    )


@router.post(
    "/sessions/{session_id}/tasks/load",
    response_model=TaskLoadResponse,
    status_code=status.HTTP_200_OK,
    summary="Load tasks for confirmed mappings",
    description="Loads O*NET tasks for all confirmed role mappings in a session.",
)
async def load_tasks_for_session(
    session_id: UUID,
    service: TaskService = Depends(get_task_service),
) -> TaskLoadResponse:
    """Load tasks for all confirmed role mappings.

    This should be called after role mappings are confirmed to populate
    the task selection table with tasks for each O*NET occupation.
    """
    result = await service.load_tasks_for_session(session_id=session_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID {session_id} not found",
        )

    return TaskLoadResponse(
        mappings_processed=result["mappings_processed"],
        tasks_loaded=result["tasks_loaded"],
    )


@router.get(
    "/sessions/{session_id}/tasks/with-dwas",
    response_model=list[TaskWithDWAsResponse],
    status_code=status.HTTP_200_OK,
    summary="Get selected tasks with DWAs",
    description="Get selected tasks with their associated DWA mappings for AI analysis.",
)
async def get_selected_tasks_with_dwas(
    session_id: UUID,
    service: TaskService = Depends(get_task_service),
) -> list[TaskWithDWAsResponse]:
    """Get selected tasks with associated DWAs for AI analysis.

    This endpoint provides the Task → DWA mapping needed for AI impact
    analysis through the DWA → IWA → GWA hierarchy.
    """
    results = await service.get_selected_tasks_with_dwas(session_id=session_id)

    return [
        TaskWithDWAsResponse(
            task_id=r["task_id"],
            description=r["description"],
            importance=r.get("importance"),
            dwa_ids=r["dwa_ids"],
        )
        for r in results
    ]
