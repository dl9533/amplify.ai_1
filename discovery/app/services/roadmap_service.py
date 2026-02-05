# discovery/app/services/roadmap_service.py
"""Roadmap service for candidate generation and prioritization."""
from typing import Any, Optional
from uuid import UUID

from app.repositories.candidate_repository import CandidateRepository
from app.repositories.analysis_repository import AnalysisRepository
from app.schemas.roadmap import BulkPhaseUpdate, RoadmapPhase


class RoadmapService:
    """Service for roadmap and candidate management."""

    def __init__(
        self,
        candidate_repository: CandidateRepository,
        analysis_repository: AnalysisRepository | None = None,
    ) -> None:
        self.candidate_repository = candidate_repository
        self.analysis_repository = analysis_repository

    async def generate_candidates(
        self,
        session_id: UUID,
    ) -> list[dict[str, Any]]:
        """Generate agentification candidates from analysis results."""
        if not self.analysis_repository:
            return []

        # Get role-dimension analysis results
        from app.models.discovery_analysis import AnalysisDimension
        results = await self.analysis_repository.get_for_session(
            session_id, AnalysisDimension.ROLE
        )

        candidates = []
        for result in results:
            # Generate agent name from role
            agent_name = self._generate_agent_name(result.dimension_value)
            description = self._generate_description(
                result.dimension_value,
                result.ai_exposure_score,
            )

            tier = result.breakdown.get("priority_tier", "future") if result.breakdown else "future"

            candidate = await self.candidate_repository.create(
                session_id=session_id,
                role_mapping_id=result.role_mapping_id,
                name=agent_name,
                description=description,
                priority_tier=tier,
                estimated_impact=result.priority_score or 0.0,
            )

            candidates.append({
                "id": str(candidate.id),
                "name": candidate.name,
                "description": candidate.description,
                "priority_tier": candidate.priority_tier.value,
                "estimated_impact": candidate.estimated_impact,
            })

        return candidates

    async def get_candidates(
        self,
        session_id: UUID,
        tier: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get candidates for a session."""
        candidates = await self.candidate_repository.get_for_session(
            session_id, tier
        )
        return [
            {
                "id": str(c.id),
                "name": c.name,
                "description": c.description,
                "priority_tier": c.priority_tier.value,
                "estimated_impact": c.estimated_impact,
                "selected_for_build": c.selected_for_build,
            }
            for c in candidates
        ]

    async def update_tier(
        self,
        candidate_id: UUID,
        tier: str,
    ) -> dict[str, Any] | None:
        """Update candidate priority tier."""
        candidate = await self.candidate_repository.update_tier(candidate_id, tier)
        if not candidate:
            return None
        return {
            "id": str(candidate.id),
            "name": candidate.name,
            "priority_tier": candidate.priority_tier.value,
        }

    async def select_for_build(
        self,
        candidate_id: UUID,
        selected: bool,
    ) -> dict[str, Any] | None:
        """Mark candidate for build."""
        candidate = await self.candidate_repository.select_for_build(
            candidate_id, selected
        )
        if not candidate:
            return None
        return {
            "id": str(candidate.id),
            "name": candidate.name,
            "selected_for_build": candidate.selected_for_build,
        }

    # Legacy methods for backward compatibility
    async def get_roadmap(
        self,
        session_id: UUID,
        phase: Optional[RoadmapPhase] = None,
    ) -> Optional[list[dict]]:
        """Get roadmap items for a session (legacy API).

        Returns items in the format expected by the roadmap router:
        - id, role_name, priority_score, priority_tier, phase, estimated_effort
        """
        tier = None
        if phase:
            tier_map = {
                RoadmapPhase.NOW: "now",
                RoadmapPhase.NEXT: "next_quarter",
                RoadmapPhase.LATER: "future",
            }
            tier = tier_map.get(phase)

        candidates = await self.candidate_repository.get_for_session(session_id, tier)

        # Map priority tier to phase
        tier_to_phase = {
            "now": "NOW",
            "next_quarter": "NEXT",
            "future": "LATER",
        }

        return [
            {
                "id": str(c.id),
                "role_name": c.name,
                "priority_score": c.estimated_impact or 0.0,
                "priority_tier": c.priority_tier.value,
                "phase": tier_to_phase.get(c.priority_tier.value, "LATER"),
                "estimated_effort": "medium",  # Default effort
                "order": None,
            }
            for c in candidates
        ]

    async def update_phase(
        self,
        item_id: UUID,
        phase: RoadmapPhase,
    ) -> Optional[dict]:
        """Update a roadmap item's phase (legacy API)."""
        tier_map = {
            RoadmapPhase.NOW: "now",
            RoadmapPhase.NEXT: "next_quarter",
            RoadmapPhase.LATER: "future",
        }
        tier = tier_map.get(phase, "future")
        return await self.update_tier(item_id, tier)

    async def reorder(
        self,
        session_id: UUID,
        item_ids: list[UUID],
    ) -> Optional[bool]:
        """Reorder roadmap items (not yet implemented)."""
        return True

    async def bulk_update(
        self,
        session_id: UUID,
        updates: list[BulkPhaseUpdate],
    ) -> Optional[int]:
        """Bulk update phases for multiple roadmap items."""
        count = 0
        for update in updates:
            result = await self.update_phase(update.id, update.phase)
            if result:
                count += 1
        return count

    def _generate_agent_name(self, role_name: str) -> str:
        """Generate agent name from role."""
        # Simple transformation: "Data Entry Clerk" -> "Data Entry Agent"
        words = role_name.split()
        if words[-1].lower() in ("clerk", "specialist", "analyst", "manager"):
            words[-1] = "Agent"
        else:
            words.append("Agent")
        return " ".join(words)

    def _generate_description(self, role_name: str, exposure: float) -> str:
        """Generate agent description."""
        exposure_pct = int(exposure * 100)
        return (
            f"AI agent to automate tasks from the {role_name} role. "
            f"Based on analysis, approximately {exposure_pct}% of work activities "
            f"are suitable for AI automation."
        )


from collections.abc import AsyncGenerator


async def get_roadmap_service() -> AsyncGenerator[RoadmapService, None]:
    """Get roadmap service dependency for FastAPI.

    Yields a fully configured RoadmapService with repositories.
    """
    from app.models.base import async_session_maker

    async with async_session_maker() as db:
        candidate_repository = CandidateRepository(db)
        analysis_repository = AnalysisRepository(db)
        service = RoadmapService(
            candidate_repository=candidate_repository,
            analysis_repository=analysis_repository,
        )
        yield service
