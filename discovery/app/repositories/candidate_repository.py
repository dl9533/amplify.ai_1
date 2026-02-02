# discovery/app/repositories/candidate_repository.py
"""Agentification candidate repository."""
from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
        tier = PriorityTier(priority_tier)
        candidate = AgentificationCandidate(
            session_id=session_id,
            role_mapping_id=role_mapping_id,
            name=name,
            description=description,
            priority_tier=tier,
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
        """Get candidates for a session."""
        stmt = select(AgentificationCandidate).where(
            AgentificationCandidate.session_id == session_id
        )
        if tier:
            stmt = stmt.where(
                AgentificationCandidate.priority_tier == PriorityTier(tier)
            )
        stmt = stmt.order_by(AgentificationCandidate.estimated_impact.desc())

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_tier(
        self,
        candidate_id: UUID,
        tier: str,
    ) -> AgentificationCandidate | None:
        """Update candidate priority tier."""
        stmt = select(AgentificationCandidate).where(
            AgentificationCandidate.id == candidate_id
        )
        result = await self.session.execute(stmt)
        candidate = result.scalar_one_or_none()

        if candidate:
            candidate.priority_tier = PriorityTier(tier)
            await self.session.commit()
            await self.session.refresh(candidate)
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
