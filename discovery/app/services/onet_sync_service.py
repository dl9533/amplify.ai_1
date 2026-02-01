"""O*NET data sync service."""
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import OnetOccupation, OnetGWA, OnetDWA
from app.services.onet_client import OnetApiClient

logger = logging.getLogger(__name__)


class OnetSyncService:
    """Service for syncing O*NET data from API to database."""

    def __init__(
        self,
        onet_client: OnetApiClient,
        db_session: AsyncSession,
    ) -> None:
        self.client = onet_client
        self.session = db_session

    async def sync_occupations(self, keywords: list[str] | None = None) -> int:
        """Sync occupations from O*NET API.

        Args:
            keywords: Optional list of keywords to search. If None, syncs common terms.

        Returns:
            Number of occupations synced.
        """
        if keywords is None:
            # Default keywords covering broad categories
            keywords = ["manager", "analyst", "engineer", "developer", "specialist"]

        synced_count = 0
        seen_codes = set()

        for keyword in keywords:
            try:
                results = await self.client.search_occupations(keyword)
                for occ in results:
                    code = occ.get("code")
                    if code and code not in seen_codes:
                        seen_codes.add(code)

                        # Upsert occupation
                        stmt = insert(OnetOccupation).values(
                            code=code,
                            title=occ.get("title", ""),
                            description=occ.get("description"),
                            updated_at=datetime.now(timezone.utc),
                        ).on_conflict_do_update(
                            index_elements=["code"],
                            set_={
                                "title": occ.get("title", ""),
                                "description": occ.get("description"),
                                "updated_at": datetime.now(timezone.utc),
                            }
                        )
                        await self.session.execute(stmt)
                        synced_count += 1

            except Exception as e:
                logger.error(f"Error syncing keyword '{keyword}': {e}")
                continue

        await self.session.commit()
        logger.info(f"Synced {synced_count} occupations")
        return synced_count

    async def sync_work_activities(self, occupation_code: str) -> int:
        """Sync work activities for a specific occupation.

        Args:
            occupation_code: O*NET occupation code.

        Returns:
            Number of activities synced.
        """
        try:
            activities = await self.client.get_work_activities(occupation_code)
            synced_count = 0

            for activity in activities:
                # Note: Actual implementation would parse GWA/IWA/DWA hierarchy
                # This is a simplified version
                activity_id = activity.get("id")
                if activity_id:
                    # For now, treat as DWA
                    stmt = insert(OnetDWA).values(
                        id=activity_id,
                        iwa_id="placeholder",  # Would need proper hierarchy
                        name=activity.get("name", ""),
                        description=activity.get("description"),
                        updated_at=datetime.now(timezone.utc),
                    ).on_conflict_do_update(
                        index_elements=["id"],
                        set_={
                            "name": activity.get("name", ""),
                            "updated_at": datetime.now(timezone.utc),
                        }
                    )
                    await self.session.execute(stmt)
                    synced_count += 1

            await self.session.commit()
            return synced_count

        except Exception as e:
            logger.error(f"Error syncing activities for {occupation_code}: {e}")
            raise

    async def full_sync(self) -> dict:
        """Perform full O*NET data sync.

        Returns:
            Dict with sync statistics.
        """
        stats = {
            "occupations": 0,
            "activities": 0,
            "errors": [],
        }

        # Sync occupations first
        stats["occupations"] = await self.sync_occupations()

        # Then sync activities for each occupation
        stmt = select(OnetOccupation.code)
        result = await self.session.execute(stmt)
        codes = result.scalars().all()

        for code in codes:
            try:
                count = await self.sync_work_activities(code)
                stats["activities"] += count
            except Exception as e:
                stats["errors"].append(f"{code}: {str(e)}")

        return stats
