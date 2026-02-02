# discovery/app/jobs/onet_sync_job.py
"""Weekly O*NET data synchronization job."""
import logging
from datetime import datetime, timezone
from typing import Any

from app.services.onet_sync_service import OnetSyncService

logger = logging.getLogger(__name__)


class OnetSyncJob:
    """Job for weekly O*NET data synchronization.

    Runs every Sunday at 2am UTC by default.
    """

    SCHEDULE_DAY = "sun"
    SCHEDULE_HOUR = 2
    SCHEDULE_MINUTE = 0

    def __init__(self, sync_service: OnetSyncService) -> None:
        self.sync_service = sync_service

    async def run(self) -> dict[str, Any]:
        """Execute the sync job.

        Returns:
            Dict with sync statistics.
        """
        start_time = datetime.now(timezone.utc)
        logger.info(f"Starting O*NET sync job at {start_time}")

        try:
            result = await self.sync_service.full_sync()

            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()

            logger.info(
                f"O*NET sync completed in {duration:.2f}s: "
                f"{result['occupations']} occupations, "
                f"{result['activities']} activities"
            )

            if result.get("errors"):
                logger.warning(f"Sync had {len(result['errors'])} errors")

            return {
                **result,
                "started_at": start_time.isoformat(),
                "completed_at": end_time.isoformat(),
                "duration_seconds": duration,
            }

        except Exception as e:
            logger.error(f"O*NET sync failed: {e}")
            raise

    @classmethod
    def get_schedule_config(cls) -> dict[str, Any]:
        """Get cron schedule configuration."""
        return {
            "day_of_week": cls.SCHEDULE_DAY,
            "hour": cls.SCHEDULE_HOUR,
            "minute": cls.SCHEDULE_MINUTE,
        }
