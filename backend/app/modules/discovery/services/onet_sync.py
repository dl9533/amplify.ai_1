"""O*NET sync job service for occupation data synchronization.

This module provides a job service for synchronizing O*NET occupation data
from the O*NET API to the local database.
"""

import logging
from typing import Any

from app.modules.discovery.repositories.onet_repository import OnetOccupationRepository
from app.modules.discovery.services.onet_client import OnetApiClient


logger = logging.getLogger(__name__)


class OnetSyncJob:
    """Job service for synchronizing O*NET occupation data.

    Fetches occupation data from the O*NET API and upserts it to the
    local database. Handles errors gracefully and tracks progress.

    Attributes:
        onet_client: Client for O*NET API requests.
        occupation_repo: Repository for occupation database operations.
    """

    def __init__(
        self,
        onet_client: OnetApiClient,
        occupation_repo: OnetOccupationRepository,
    ) -> None:
        """Initialize the sync job.

        Args:
            onet_client: O*NET API client instance.
            occupation_repo: Occupation repository instance.
        """
        self.onet_client = onet_client
        self.occupation_repo = occupation_repo

    async def sync_occupations(self, keyword: str = "") -> dict[str, Any]:
        """Synchronize occupations from O*NET API to database.

        Fetches occupations from the O*NET API and upserts them to the
        local database. Tracks progress and handles errors gracefully.

        Args:
            keyword: Optional search keyword to filter occupations.
                    Defaults to empty string for broad search.

        Returns:
            Dictionary with sync results containing:
            - success: Whether the sync completed successfully.
            - processed_count: Number of occupations processed.
            - error: Error message if sync failed (only present on failure).
        """
        try:
            occupations = await self.onet_client.search_occupations(keyword)

            processed_count = 0
            for occupation in occupations:
                code = occupation.get("code")
                title = occupation.get("title")
                description = occupation.get("description")

                if code and title:
                    await self.occupation_repo.upsert(
                        code=code,
                        title=title,
                        description=description,
                    )
                    processed_count += 1

            logger.info(
                "O*NET occupation sync completed: %d occupations processed",
                processed_count,
            )

            return {
                "success": True,
                "processed_count": processed_count,
            }

        except Exception as e:
            error_message = str(e)
            logger.error("O*NET occupation sync failed: %s", error_message)

            return {
                "success": False,
                "processed_count": 0,
                "error": error_message,
            }
