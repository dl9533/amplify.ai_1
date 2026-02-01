"""Agentification candidate repository for database operations.

Provides the AgentificationCandidateRepository for managing candidate
records including CRUD operations, priority tier filtering, and build selection.
"""

from uuid import UUID

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.discovery.enums import PriorityTier
from app.modules.discovery.models.session import AgentificationCandidate


def _validate_estimated_impact(impact: float | None, allow_none: bool = False) -> None:
    """Validate that estimated impact is within valid range.

    Args:
        impact: Estimated impact score to validate.
        allow_none: Whether None is a valid value.

    Raises:
        ValueError: If impact is outside the valid range (0.0-1.0) or None when required.
    """
    if impact is None:
        if not allow_none:
            raise ValueError("estimated_impact is required")
        return
    if impact < 0.0 or impact > 1.0:
        raise ValueError(f"estimated_impact must be between 0.0 and 1.0, got {impact}")


class AgentificationCandidateRepository:
    """Repository for AgentificationCandidate CRUD and query operations.

    Provides async database operations for agentification candidates including:
    - Create new candidates with priority tier and impact estimates
    - Retrieve candidates by ID, session, role mapping, or priority tier
    - Update priority tier, details, and build selection status
    - Link candidates to intake requests
    - Bulk update operations
    - Delete candidates
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy async session for database operations.
        """
        self.session = session

    async def create(
        self,
        session_id: UUID,
        role_mapping_id: UUID,
        name: str,
        priority_tier: PriorityTier,
        estimated_impact: float,
        description: str | None = None,
        selected_for_build: bool = False,
    ) -> AgentificationCandidate:
        """Create a new agentification candidate.

        Creates a candidate representing a recommended agent that could be built
        based on discovery analysis.

        Args:
            session_id: UUID of the discovery session this candidate belongs to.
            role_mapping_id: UUID of the role mapping this candidate is based on.
            name: Name of the candidate agent.
            priority_tier: Timeline bucket for implementation (NOW, NEXT_QUARTER, FUTURE).
            estimated_impact: Estimated impact score (0.0-1.0).
            description: Optional description of the candidate.
            selected_for_build: Whether the candidate is selected for building.

        Returns:
            The created AgentificationCandidate instance.

        Raises:
            ValueError: If estimated_impact is outside the range 0.0-1.0 or None.
        """
        _validate_estimated_impact(estimated_impact, allow_none=False)
        candidate = AgentificationCandidate(
            session_id=session_id,
            role_mapping_id=role_mapping_id,
            name=name,
            description=description,
            priority_tier=priority_tier,
            estimated_impact=estimated_impact,
            selected_for_build=selected_for_build,
        )
        self.session.add(candidate)
        await self.session.commit()
        await self.session.refresh(candidate)
        return candidate

    async def get_by_id(self, candidate_id: UUID) -> AgentificationCandidate | None:
        """Retrieve a candidate by its ID.

        Args:
            candidate_id: UUID of the candidate to retrieve.

        Returns:
            AgentificationCandidate if found, None otherwise.
        """
        stmt = select(AgentificationCandidate).where(
            AgentificationCandidate.id == candidate_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_session_id(
        self, session_id: UUID
    ) -> list[AgentificationCandidate]:
        """Retrieve all candidates for a specific session.

        Args:
            session_id: UUID of the session whose candidates to retrieve.

        Returns:
            List of AgentificationCandidate instances for the session.
        """
        stmt = select(AgentificationCandidate).where(
            AgentificationCandidate.session_id == session_id
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_priority_tier(
        self, session_id: UUID, priority_tier: PriorityTier
    ) -> list[AgentificationCandidate]:
        """Retrieve candidates filtered by priority tier.

        Args:
            session_id: UUID of the session to filter within.
            priority_tier: PriorityTier enum value to filter by.

        Returns:
            List of AgentificationCandidate instances matching the tier.
        """
        stmt = select(AgentificationCandidate).where(
            and_(
                AgentificationCandidate.session_id == session_id,
                AgentificationCandidate.priority_tier == priority_tier,
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_priority_tier(
        self, candidate_id: UUID, priority_tier: PriorityTier
    ) -> AgentificationCandidate | None:
        """Update the priority tier for a candidate.

        Args:
            candidate_id: UUID of the candidate to update.
            priority_tier: New PriorityTier value.

        Returns:
            Updated AgentificationCandidate if found, None otherwise.
        """
        candidate = await self.get_by_id(candidate_id)
        if candidate is None:
            return None

        candidate.priority_tier = priority_tier
        await self.session.commit()
        await self.session.refresh(candidate)
        return candidate

    async def update_details(
        self,
        candidate_id: UUID,
        name: str | None = None,
        description: str | None = None,
    ) -> AgentificationCandidate | None:
        """Update candidate name and/or description.

        Args:
            candidate_id: UUID of the candidate to update.
            name: Optional new name for the candidate.
            description: Optional new description for the candidate.

        Returns:
            Updated AgentificationCandidate if found, None otherwise.
        """
        candidate = await self.get_by_id(candidate_id)
        if candidate is None:
            return None

        if name is not None:
            candidate.name = name
        if description is not None:
            candidate.description = description

        await self.session.commit()
        await self.session.refresh(candidate)
        return candidate

    async def select_for_build(
        self, candidate_id: UUID
    ) -> AgentificationCandidate | None:
        """Set selected_for_build to True.

        Args:
            candidate_id: UUID of the candidate to select.

        Returns:
            Updated AgentificationCandidate if found, None otherwise.
        """
        candidate = await self.get_by_id(candidate_id)
        if candidate is None:
            return None

        candidate.selected_for_build = True
        await self.session.commit()
        await self.session.refresh(candidate)
        return candidate

    async def deselect_for_build(
        self, candidate_id: UUID
    ) -> AgentificationCandidate | None:
        """Set selected_for_build to False.

        Args:
            candidate_id: UUID of the candidate to deselect.

        Returns:
            Updated AgentificationCandidate if found, None otherwise.
        """
        candidate = await self.get_by_id(candidate_id)
        if candidate is None:
            return None

        candidate.selected_for_build = False
        await self.session.commit()
        await self.session.refresh(candidate)
        return candidate

    async def link_intake_request(
        self, candidate_id: UUID, intake_request_id: UUID
    ) -> AgentificationCandidate | None:
        """Link a candidate to an intake request.

        Args:
            candidate_id: UUID of the candidate to link.
            intake_request_id: UUID of the intake request to link to.

        Returns:
            Updated AgentificationCandidate if found, None otherwise.
        """
        candidate = await self.get_by_id(candidate_id)
        if candidate is None:
            return None

        candidate.intake_request_id = intake_request_id
        await self.session.commit()
        await self.session.refresh(candidate)
        return candidate

    async def get_selected_for_build(
        self, session_id: UUID
    ) -> list[AgentificationCandidate]:
        """Get all candidates selected for build in a session.

        Args:
            session_id: UUID of the session to filter within.

        Returns:
            List of AgentificationCandidate instances with selected_for_build=True.
        """
        stmt = select(AgentificationCandidate).where(
            and_(
                AgentificationCandidate.session_id == session_id,
                AgentificationCandidate.selected_for_build.is_(True),
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_role_mapping_id(
        self, role_mapping_id: UUID
    ) -> list[AgentificationCandidate]:
        """Retrieve all candidates for a specific role mapping.

        Args:
            role_mapping_id: UUID of the role mapping whose candidates to retrieve.

        Returns:
            List of AgentificationCandidate instances for the role mapping.
        """
        stmt = select(AgentificationCandidate).where(
            AgentificationCandidate.role_mapping_id == role_mapping_id
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, candidate_id: UUID) -> bool:
        """Delete a candidate by its ID.

        Args:
            candidate_id: UUID of the candidate to delete.

        Returns:
            True if the candidate was deleted, False if not found.
        """
        candidate = await self.get_by_id(candidate_id)
        if candidate is None:
            return False

        await self.session.delete(candidate)
        await self.session.commit()
        return True

    async def bulk_update_priority_tier(
        self, candidate_ids: list[UUID], priority_tier: PriorityTier
    ) -> int:
        """Bulk update priority tier for multiple candidates.

        Uses a single UPDATE statement for efficiency.

        Args:
            candidate_ids: List of UUIDs of candidates to update.
            priority_tier: New PriorityTier value for all candidates.

        Returns:
            Number of candidates actually updated.
        """
        if not candidate_ids:
            return 0

        stmt = (
            update(AgentificationCandidate)
            .where(AgentificationCandidate.id.in_(candidate_ids))
            .values(priority_tier=priority_tier)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount
