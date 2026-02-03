"""Admin router for the Discovery module."""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.base import async_session_maker
from app.repositories.onet_repository import OnetRepository
from app.schemas.admin import OnetSyncRequest, OnetSyncResponse, OnetSyncStatus
from app.services.onet_file_sync_service import (
    OnetFileSyncService,
    OnetSyncError,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/discovery/admin",
    tags=["admin"],
)


async def get_onet_sync_service() -> OnetFileSyncService:
    """Get O*NET sync service dependency."""
    async with async_session_maker() as db:
        repository = OnetRepository(db)
        yield OnetFileSyncService(repository=repository)


@router.post(
    "/onet/sync",
    response_model=OnetSyncResponse,
    status_code=status.HTTP_200_OK,
    summary="Sync O*NET database",
    description="Downloads and imports the O*NET database from official release files.",
)
async def sync_onet_database(
    request: OnetSyncRequest,
    service: Annotated[OnetFileSyncService, Depends(get_onet_sync_service)],
) -> OnetSyncResponse:
    """Sync O*NET database from official files.

    Downloads the specified version of the O*NET database and imports
    occupations, alternate titles, and tasks into the local database.
    """
    try:
        result = await service.sync(version=request.version)
        return OnetSyncResponse(
            version=result.version,
            occupation_count=result.occupation_count,
            alternate_title_count=result.alternate_title_count,
            task_count=result.task_count,
            status=result.status,
        )
    except OnetSyncError as e:
        logger.error(f"O*NET sync failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/onet/status",
    response_model=OnetSyncStatus,
    status_code=status.HTTP_200_OK,
    summary="Get O*NET sync status",
    description="Returns the current O*NET database sync status.",
)
async def get_onet_sync_status(
    service: Annotated[OnetFileSyncService, Depends(get_onet_sync_service)],
) -> OnetSyncStatus:
    """Get current O*NET sync status."""
    status_data = await service.get_sync_status()
    return OnetSyncStatus(
        synced=status_data["synced"],
        version=status_data["version"],
        synced_at=status_data["synced_at"],
        occupation_count=status_data["occupation_count"],
    )
