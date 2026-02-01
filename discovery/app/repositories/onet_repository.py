"""O*NET data repository."""
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import OnetOccupation, OnetGWA, OnetIWA, OnetDWA


class OnetRepository:
    """Repository for O*NET reference data operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def search_occupations(
        self,
        keyword: str,
        limit: int = 20,
    ) -> Sequence[OnetOccupation]:
        """Search occupations by keyword in title."""
        stmt = (
            select(OnetOccupation)
            .where(OnetOccupation.title.ilike(f"%{keyword}%"))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_code(self, code: str) -> OnetOccupation | None:
        """Get occupation by O*NET code."""
        stmt = select(OnetOccupation).where(OnetOccupation.code == code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_gwas(self) -> Sequence[OnetGWA]:
        """Get all Generalized Work Activities."""
        stmt = select(OnetGWA).order_by(OnetGWA.name)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_dwas_for_occupation(
        self,
        occupation_code: str,
    ) -> Sequence[OnetDWA]:
        """Get DWAs associated with an occupation through tasks."""
        # This will be implemented with proper joins once task-to-dwa mapping exists
        stmt = select(OnetDWA).order_by(OnetDWA.name)
        result = await self.session.execute(stmt)
        return result.scalars().all()
