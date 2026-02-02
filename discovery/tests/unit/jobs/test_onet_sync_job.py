# discovery/tests/unit/jobs/test_onet_sync_job.py
"""Unit tests for O*NET sync job."""
import pytest
from unittest.mock import AsyncMock


def test_onet_sync_job_exists():
    """Test OnetSyncJob is importable."""
    from app.jobs.onet_sync_job import OnetSyncJob
    assert OnetSyncJob is not None


@pytest.mark.asyncio
async def test_run_sync():
    """Test running the sync job."""
    from app.jobs.onet_sync_job import OnetSyncJob

    mock_sync_service = AsyncMock()
    mock_sync_service.full_sync.return_value = {
        "occupations": 100,
        "activities": 500,
        "errors": [],
    }

    job = OnetSyncJob(sync_service=mock_sync_service)
    result = await job.run()

    assert result["occupations"] == 100
    mock_sync_service.full_sync.assert_called_once()


def test_job_schedule_config():
    """Test job has correct schedule config."""
    from app.jobs.onet_sync_job import OnetSyncJob

    # Default: Sunday 2am UTC
    assert OnetSyncJob.SCHEDULE_DAY == "sun"
    assert OnetSyncJob.SCHEDULE_HOUR == 2


def test_get_schedule_config():
    """Test get_schedule_config returns dict."""
    from app.jobs.onet_sync_job import OnetSyncJob

    config = OnetSyncJob.get_schedule_config()
    assert "day_of_week" in config
    assert "hour" in config
