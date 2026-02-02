# discovery/app/jobs/scheduler.py
"""Job scheduler using APScheduler."""
import logging
from typing import Callable, Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)


class JobScheduler:
    """Async job scheduler for background tasks."""

    def __init__(self) -> None:
        self._scheduler = AsyncIOScheduler()
        self._jobs: dict[str, Any] = {}

    def add_job(
        self,
        job_id: str,
        func: Callable,
        trigger: str = "interval",
        **trigger_args,
    ) -> None:
        """Add a job to the scheduler.

        Args:
            job_id: Unique job identifier.
            func: Async function to execute.
            trigger: 'interval' or 'cron'.
            **trigger_args: Arguments for the trigger (hours, minutes, day_of_week, etc.)
        """
        if trigger == "cron":
            trigger_obj = CronTrigger(**trigger_args)
        else:
            trigger_obj = IntervalTrigger(**trigger_args)

        job = self._scheduler.add_job(
            func,
            trigger=trigger_obj,
            id=job_id,
            replace_existing=True,
        )
        self._jobs[job_id] = job
        logger.info(f"Added job: {job_id}")

    def remove_job(self, job_id: str) -> bool:
        """Remove a job from the scheduler."""
        if job_id in self._jobs:
            self._scheduler.remove_job(job_id)
            del self._jobs[job_id]
            return True
        return False

    def start(self) -> None:
        """Start the scheduler."""
        if not self._scheduler.running:
            self._scheduler.start()
            logger.info("Job scheduler started")

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the scheduler."""
        if self._scheduler.running:
            self._scheduler.shutdown(wait=wait)
            logger.info("Job scheduler stopped")

    def get_jobs(self) -> list[dict[str, Any]]:
        """Get list of scheduled jobs."""
        return [
            {
                "id": job.id,
                "next_run": str(job.next_run_time) if job.next_run_time else None,
            }
            for job in self._scheduler.get_jobs()
        ]
