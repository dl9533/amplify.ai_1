"""Discovery session repository for database operations.

Provides the DiscoverySessionRepository for managing discovery session
records including CRUD operations and user-specific queries.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.discovery.enums import SessionStatus
from app.modules.discovery.models.session import DiscoverySession


class DiscoverySessionRepository:
    """Repository for DiscoverySession CRUD and query operations.

    Provides async database operations for discovery sessions including:
    - Create new sessions with default DRAFT status
    - Retrieve sessions by ID
    - Update session step and status
    - List sessions for a specific user
    - Delete sessions
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy async session for database operations.
        """
        self.session = session

    async def create(
        self,
        user_id: UUID,
        organization_id: UUID,
    ) -> DiscoverySession:
        """Create a new discovery session.

        Creates a session with default DRAFT status and step 1.

        Args:
            user_id: UUID of the user creating the session.
            organization_id: UUID of the organization for the session.

        Returns:
            The created DiscoverySession instance.
        """
        discovery_session = DiscoverySession(
            user_id=user_id,
            organization_id=organization_id,
            status=SessionStatus.DRAFT,
            current_step=1,
        )
        self.session.add(discovery_session)
        await self.session.commit()
        await self.session.refresh(discovery_session)
        return discovery_session

    async def get_by_id(self, session_id: UUID) -> DiscoverySession | None:
        """Retrieve a discovery session by its ID.

        Args:
            session_id: UUID of the session to retrieve.

        Returns:
            DiscoverySession if found, None otherwise.
        """
        stmt = select(DiscoverySession).where(DiscoverySession.id == session_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_step(
        self,
        session_id: UUID,
        step: int,
    ) -> DiscoverySession | None:
        """Update the current step of a discovery session.

        Args:
            session_id: UUID of the session to update.
            step: The new step number.

        Returns:
            Updated DiscoverySession if found, None otherwise.
        """
        discovery_session = await self.get_by_id(session_id)
        if discovery_session is None:
            return None

        discovery_session.current_step = step
        await self.session.commit()
        await self.session.refresh(discovery_session)
        return discovery_session

    async def update_status(
        self,
        session_id: UUID,
        status: SessionStatus,
    ) -> DiscoverySession | None:
        """Update the status of a discovery session.

        Args:
            session_id: UUID of the session to update.
            status: The new session status.

        Returns:
            Updated DiscoverySession if found, None otherwise.
        """
        discovery_session = await self.get_by_id(session_id)
        if discovery_session is None:
            return None

        discovery_session.status = status
        await self.session.commit()
        await self.session.refresh(discovery_session)
        return discovery_session

    async def list_for_user(self, user_id: UUID) -> list[DiscoverySession]:
        """List all discovery sessions for a specific user.

        Args:
            user_id: UUID of the user whose sessions to list.

        Returns:
            List of DiscoverySession instances for the user.
        """
        stmt = select(DiscoverySession).where(DiscoverySession.user_id == user_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, session_id: UUID) -> bool:
        """Delete a discovery session by its ID.

        Args:
            session_id: UUID of the session to delete.

        Returns:
            True if the session was deleted, False if not found.
        """
        discovery_session = await self.get_by_id(session_id)
        if discovery_session is None:
            return False

        await self.session.delete(discovery_session)
        await self.session.commit()
        return True
