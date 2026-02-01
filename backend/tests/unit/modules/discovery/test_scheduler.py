# backend/tests/unit/modules/discovery/test_scheduler.py
"""Unit tests for O*NET sync scheduler."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.modules.discovery.jobs.scheduler import OnetSyncScheduler
from app.modules.discovery.services.onet_sync import OnetSyncJob


@pytest.fixture
def mock_sync_job():
    """Create a mock OnetSyncJob."""
    mock = MagicMock(spec=OnetSyncJob)
    mock.sync_occupations = AsyncMock(
        return_value={"success": True, "processed_count": 10, "skipped_count": 0}
    )
    return mock


def test_scheduler_initializes(mock_sync_job):
    """Scheduler should initialize with APScheduler and sync job."""
    scheduler = OnetSyncScheduler(sync_job=mock_sync_job)
    assert scheduler is not None
    assert scheduler._sync_job is mock_sync_job


def test_scheduler_weekly_job_configured(mock_sync_job):
    """Scheduler should have weekly job configured for Sunday 2am UTC."""
    scheduler = OnetSyncScheduler(sync_job=mock_sync_job)

    job = scheduler.get_job("onet_weekly_sync")
    assert job is not None


def test_scheduler_can_trigger_manual_sync(mock_sync_job):
    """Scheduler should allow manual sync trigger and return result."""
    scheduler = OnetSyncScheduler(sync_job=mock_sync_job)

    result = scheduler.trigger_manual_sync()

    mock_sync_job.sync_occupations.assert_called_once()
    assert result["success"] is True
    assert result["processed_count"] == 10


def test_trigger_manual_sync_returns_result(mock_sync_job):
    """trigger_manual_sync should return the sync result dictionary."""
    mock_sync_job.sync_occupations = AsyncMock(
        return_value={"success": True, "processed_count": 5, "skipped_count": 2}
    )
    scheduler = OnetSyncScheduler(sync_job=mock_sync_job)

    result = scheduler.trigger_manual_sync()

    assert isinstance(result, dict)
    assert result["success"] is True
    assert result["processed_count"] == 5
    assert result["skipped_count"] == 2


def test_run_sync_handles_errors_gracefully(mock_sync_job):
    """_run_sync should catch exceptions and return error dict."""
    mock_sync_job.sync_occupations = AsyncMock(
        side_effect=Exception("API connection failed")
    )
    scheduler = OnetSyncScheduler(sync_job=mock_sync_job)

    result = scheduler._run_sync()

    assert result["success"] is False
    assert "error" in result
    assert "API connection failed" in result["error"]


def test_scheduler_start_and_shutdown(mock_sync_job):
    """Scheduler should start and shutdown cleanly."""
    scheduler = OnetSyncScheduler(sync_job=mock_sync_job)

    scheduler.start()
    assert scheduler.is_running()

    scheduler.shutdown()
    assert not scheduler.is_running()


def test_scheduler_start_idempotent(mock_sync_job):
    """Calling start() multiple times should not cause errors."""
    scheduler = OnetSyncScheduler(sync_job=mock_sync_job)

    scheduler.start()
    assert scheduler.is_running()

    # Second start should be a no-op
    scheduler.start()
    assert scheduler.is_running()

    scheduler.shutdown()
    assert not scheduler.is_running()


def test_scheduler_shutdown_idempotent(mock_sync_job):
    """Calling shutdown() multiple times should not cause errors."""
    scheduler = OnetSyncScheduler(sync_job=mock_sync_job)

    scheduler.start()
    assert scheduler.is_running()

    scheduler.shutdown()
    assert not scheduler.is_running()

    # Second shutdown should be a no-op
    scheduler.shutdown()
    assert not scheduler.is_running()


def test_get_job_returns_none_for_invalid_id(mock_sync_job):
    """get_job should return None for non-existent job ID."""
    scheduler = OnetSyncScheduler(sync_job=mock_sync_job)

    job = scheduler.get_job("nonexistent_job")
    assert job is None


def test_get_job_returns_job_for_valid_id(mock_sync_job):
    """get_job should return the job for a valid job ID."""
    scheduler = OnetSyncScheduler(sync_job=mock_sync_job)

    job = scheduler.get_job(OnetSyncScheduler.JOB_ID)
    assert job is not None
    assert job.id == OnetSyncScheduler.JOB_ID
