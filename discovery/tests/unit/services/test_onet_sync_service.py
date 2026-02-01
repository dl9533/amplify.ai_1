"""Unit tests for O*NET sync service."""
import pytest
from unittest.mock import AsyncMock, MagicMock


def test_onet_sync_service_exists():
    """Test OnetSyncService is importable."""
    from app.services.onet_sync_service import OnetSyncService
    assert OnetSyncService is not None


@pytest.mark.asyncio
async def test_sync_occupations():
    """Test sync_occupations method exists."""
    from app.services.onet_sync_service import OnetSyncService

    mock_client = AsyncMock()
    mock_session = AsyncMock()

    service = OnetSyncService(
        onet_client=mock_client,
        db_session=mock_session,
    )

    assert hasattr(service, "sync_occupations")


@pytest.mark.asyncio
async def test_sync_work_activities():
    """Test sync_work_activities method exists."""
    from app.services.onet_sync_service import OnetSyncService

    mock_client = AsyncMock()
    mock_session = AsyncMock()

    service = OnetSyncService(
        onet_client=mock_client,
        db_session=mock_session,
    )

    assert hasattr(service, "sync_work_activities")


@pytest.mark.asyncio
async def test_full_sync():
    """Test full_sync method exists."""
    from app.services.onet_sync_service import OnetSyncService

    mock_client = AsyncMock()
    mock_session = AsyncMock()

    service = OnetSyncService(
        onet_client=mock_client,
        db_session=mock_session,
    )

    assert hasattr(service, "full_sync")
