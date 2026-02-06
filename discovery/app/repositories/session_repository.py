"""Discovery session repository."""
from typing import Sequence
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.discovery_session import DiscoverySession, SessionStatus


class SessionRepository:
    """Repository for discovery session operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        user_id: UUID,
        organization_id: UUID,
        industry_naics_sector: str | None = None,
    ) -> DiscoverySession:
        """Create a new discovery session."""
        db_session = DiscoverySession(
            user_id=user_id,
            organization_id=organization_id,
            status=SessionStatus.PENDING,
            current_step=1,
            industry_naics_sector=industry_naics_sector,
        )
        self.session.add(db_session)
        await self.session.commit()
        await self.session.refresh(db_session)
        return db_session

    async def get_by_id(self, session_id: UUID) -> DiscoverySession | None:
        """Get session by ID."""
        stmt = select(DiscoverySession).where(DiscoverySession.id == session_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        user_id: UUID,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[Sequence[DiscoverySession], int]:
        """List sessions for a user with pagination."""
        offset = (page - 1) * per_page

        # Get total count
        count_stmt = (
            select(func.count())
            .select_from(DiscoverySession)
            .where(DiscoverySession.user_id == user_id)
        )
        total = await self.session.scalar(count_stmt) or 0

        # Get paginated results
        stmt = (
            select(DiscoverySession)
            .where(DiscoverySession.user_id == user_id)
            .order_by(DiscoverySession.updated_at.desc())
            .offset(offset)
            .limit(per_page)
        )
        result = await self.session.execute(stmt)
        sessions = result.scalars().all()

        return sessions, total

    async def update_step(
        self,
        session_id: UUID,
        step: int,
    ) -> DiscoverySession | None:
        """Update session current step."""
        db_session = await self.get_by_id(session_id)
        if db_session:
            db_session.current_step = step
            if step > 1:
                db_session.status = SessionStatus.UPLOAD_COMPLETE
            await self.session.commit()
            await self.session.refresh(db_session)
        return db_session

    async def update_industry(
        self,
        session_id: UUID,
        industry_naics_sector: str | None,
    ) -> DiscoverySession | None:
        """Update session industry NAICS sector (None to clear)."""
        db_session = await self.get_by_id(session_id)
        if db_session:
            db_session.industry_naics_sector = industry_naics_sector
            await self.session.commit()
            await self.session.refresh(db_session)
        return db_session

    async def delete(self, session_id: UUID) -> bool:
        """Delete a session."""
        db_session = await self.get_by_id(session_id)
        if db_session:
            await self.session.delete(db_session)
            await self.session.commit()
            return True
        return False
