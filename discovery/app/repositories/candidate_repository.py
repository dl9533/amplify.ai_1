# discovery/app/repositories/candidate_repository.py
"""Agentification candidate repository."""
from typing import Sequence
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.agentification_candidate import AgentificationCandidate, PriorityTier


class CandidateRepository:
    """Repository for agentification candidates."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        session_id: UUID,
        role_mapping_id: UUID | None,
        name: str,
        description: str | None,
        priority_tier: str,
        estimated_impact: float,
    ) -> AgentificationCandidate:
        """Create a new candidate."""
        # Validate tier value
        tier = PriorityTier(priority_tier)
        candidate = AgentificationCandidate(
            session_id=session_id,
            role_mapping_id=role_mapping_id,
            name=name,
            description=description,
            priority_tier=tier.value,  # Use the string value for PostgreSQL enum
            estimated_impact=estimated_impact,
        )
        self.session.add(candidate)
        await self.session.commit()
        await self.session.refresh(candidate)
        return candidate

    async def get_for_session(
        self,
        session_id: UUID,
        tier: str | None = None,
    ) -> Sequence[AgentificationCandidate]:
        """Get candidates for a session.

        Orders by display_order first (if set), then by estimated_impact descending.
        This ensures manual reordering is respected while new candidates
        appear sorted by impact.
        """
        stmt = select(AgentificationCandidate).where(
            AgentificationCandidate.session_id == session_id
        )
        if tier:
            # Validate tier value and use string value for comparison
            validated_tier = PriorityTier(tier).value
            stmt = stmt.where(
                AgentificationCandidate.priority_tier == validated_tier
            )
        # Order by display_order (nulls last), then by estimated_impact
        stmt = stmt.order_by(
            AgentificationCandidate.display_order.asc().nulls_last(),
            AgentificationCandidate.estimated_impact.desc(),
        )

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_tier(
        self,
        candidate_id: UUID,
        tier: str,
    ) -> AgentificationCandidate | None:
        """Update candidate priority tier."""
        stmt = (
            select(AgentificationCandidate)
            .options(selectinload(AgentificationCandidate.role_mapping))
            .where(AgentificationCandidate.id == candidate_id)
        )
        result = await self.session.execute(stmt)
        candidate = result.scalar_one_or_none()

        if candidate:
            # Validate tier value and use string value for PostgreSQL enum
            candidate.priority_tier = PriorityTier(tier).value
            await self.session.commit()
            await self.session.refresh(candidate, ["role_mapping"])
        return candidate

    async def select_for_build(
        self,
        candidate_id: UUID,
        selected: bool,
    ) -> AgentificationCandidate | None:
        """Mark candidate for build."""
        stmt = select(AgentificationCandidate).where(
            AgentificationCandidate.id == candidate_id
        )
        result = await self.session.execute(stmt)
        candidate = result.scalar_one_or_none()

        if candidate:
            candidate.selected_for_build = selected
            await self.session.commit()
            await self.session.refresh(candidate)
        return candidate

    async def delete_for_session(
        self,
        session_id: UUID,
    ) -> int:
        """Delete all candidates for a session.

        Used to clear existing candidates before regenerating to prevent duplicates.

        Args:
            session_id: The session ID to delete candidates for.

        Returns:
            Number of candidates deleted.
        """
        stmt = delete(AgentificationCandidate).where(
            AgentificationCandidate.session_id == session_id
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount or 0

    async def reorder(
        self,
        session_id: UUID,
        item_ids: list[UUID],
    ) -> bool:
        """Reorder candidates by updating their display_order.

        Sets display_order based on position in item_ids list.
        Only updates candidates belonging to the specified session.

        Args:
            session_id: The session ID (for authorization validation).
            item_ids: Ordered list of candidate IDs.

        Returns:
            True if all candidates were updated, False if some not found.
        """
        if not item_ids:
            return True

        # Update each candidate's display_order based on position
        for order, candidate_id in enumerate(item_ids):
            stmt = (
                update(AgentificationCandidate)
                .where(
                    AgentificationCandidate.id == candidate_id,
                    AgentificationCandidate.session_id == session_id,
                )
                .values(display_order=order)
            )
            await self.session.execute(stmt)

        await self.session.commit()
        return True
