"""O*NET sync scheduler for weekly occupation data synchronization.

This module provides a scheduler using APScheduler to run the OnetSyncJob
weekly on Sunday at 2am UTC.
"""

import logging
from typing import Any

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger


logger = logging.getLogger(__name__)


class OnetSyncScheduler:
    """Scheduler for O*NET weekly sync job.

    Uses APScheduler to schedule and manage the weekly O*NET occupation
    data synchronization job. The job runs every Sunday at 2am UTC.

    Attributes:
        scheduler: The APScheduler BackgroundScheduler instance.
    """

    JOB_ID = "onet_weekly_sync"

    def __init__(self) -> None:
        """Initialize the scheduler with APScheduler.

        Creates a BackgroundScheduler and configures the weekly sync job
        to run every Sunday at 2am UTC.
        """
        self._scheduler = BackgroundScheduler(timezone="UTC")
        self._configure_jobs()

    def _configure_jobs(self) -> None:
        """Configure the scheduled jobs.

        Adds the weekly sync job scheduled for Sunday at 2am UTC.
        """
        # Schedule weekly sync job: Sunday at 2:00 AM UTC
        self._scheduler.add_job(
            func=self._run_sync,
            trigger=CronTrigger(
                day_of_week="sun",
                hour=2,
                minute=0,
                timezone="UTC",
            ),
            id=self.JOB_ID,
            name="O*NET Weekly Sync",
            replace_existing=True,
        )
        logger.info("Configured O*NET weekly sync job for Sunday 2am UTC")

    def _run_sync(self) -> dict[str, Any]:
        """Execute the O*NET sync job.

        This method is called by the scheduler to run the sync.
        Override or extend this method to provide actual sync implementation.

        Returns:
            Dictionary with sync results.
        """
        logger.info("Starting O*NET weekly sync job")
        # The actual sync implementation will be injected or configured
        # This is a placeholder for the scheduled execution
        return {"success": True, "message": "Sync triggered"}

    def get_job(self, job_id: str) -> Any:
        """Get a scheduled job by its ID.

        Args:
            job_id: The unique identifier of the job.

        Returns:
            The job instance if found, None otherwise.
        """
        return self._scheduler.get_job(job_id)

    def trigger_manual_sync(self) -> None:
        """Trigger a manual sync outside of the schedule.

        Allows administrators to manually trigger a sync when needed,
        without waiting for the scheduled weekly run.
        """
        logger.info("Manual O*NET sync triggered")
        self._run_sync()

    def start(self) -> None:
        """Start the scheduler.

        Begins execution of scheduled jobs. The scheduler will run
        in the background until shutdown() is called.
        """
        if not self._scheduler.running:
            self._scheduler.start()
            logger.info("O*NET sync scheduler started")

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the scheduler.

        Stops all scheduled jobs and cleans up resources.

        Args:
            wait: If True, wait for running jobs to complete before shutdown.
        """
        if self._scheduler.running:
            self._scheduler.shutdown(wait=wait)
            logger.info("O*NET sync scheduler shut down")

    def is_running(self) -> bool:
        """Check if the scheduler is currently running.

        Returns:
            True if the scheduler is running, False otherwise.
        """
        return self._scheduler.running
