# backend/tests/unit/modules/discovery/test_scheduler.py
import pytest
from unittest.mock import MagicMock, patch

from app.modules.discovery.jobs.scheduler import OnetSyncScheduler


def test_scheduler_initializes():
    """Scheduler should initialize with APScheduler."""
    scheduler = OnetSyncScheduler()
    assert scheduler is not None


def test_scheduler_weekly_job_configured():
    """Scheduler should have weekly job configured for Sunday 2am UTC."""
    scheduler = OnetSyncScheduler()

    job = scheduler.get_job("onet_weekly_sync")
    assert job is not None


def test_scheduler_can_trigger_manual_sync():
    """Scheduler should allow manual sync trigger."""
    scheduler = OnetSyncScheduler()

    with patch.object(scheduler, "_run_sync") as mock_run:
        scheduler.trigger_manual_sync()
        mock_run.assert_called_once()


def test_scheduler_start_and_shutdown():
    """Scheduler should start and shutdown cleanly."""
    scheduler = OnetSyncScheduler()

    scheduler.start()
    assert scheduler.is_running()

    scheduler.shutdown()
    assert not scheduler.is_running()
