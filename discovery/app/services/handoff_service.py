# discovery/app/services/handoff_service.py
"""Handoff service for Build intake integration."""
from typing import Any, Optional
from uuid import UUID

from app.repositories.candidate_repository import CandidateRepository
from app.repositories.session_repository import SessionRepository
from app.schemas.handoff import (
    HandoffRequest,
    HandoffResponse,
    HandoffStatus,
    ValidationResult,
)


class HandoffService:
    """Service for creating handoff bundles to Build workflow."""

    def __init__(
        self,
        candidate_repository: CandidateRepository,
        session_repository: SessionRepository | None = None,
    ) -> None:
        self.candidate_repository = candidate_repository
        self.session_repository = session_repository

    async def create_handoff_bundle(
        self,
        session_id: UUID,
    ) -> dict[str, Any]:
        """Create handoff bundle for selected candidates.

        Returns bundle with candidate details for Build intake.
        """
        # Get selected candidates
        all_candidates = await self.candidate_repository.get_for_session(session_id)
        selected = [c for c in all_candidates if c.selected_for_build]

        if not selected:
            return {"error": "No candidates selected for build", "candidates": []}

        candidates_data = []
        for c in selected:
            candidates_data.append({
                "id": str(c.id),
                "name": c.name,
                "description": c.description,
                "priority_tier": c.priority_tier.value,
                "estimated_impact": c.estimated_impact,
                "role_mapping_id": str(c.role_mapping_id) if c.role_mapping_id else None,
            })

        return {
            "session_id": str(session_id),
            "candidates": candidates_data,
            "count": len(candidates_data),
        }

    async def complete_handoff(
        self,
        session_id: UUID,
        intake_request_ids: dict[str, UUID],
    ) -> dict[str, Any]:
        """Mark handoff complete with intake request IDs.

        Args:
            session_id: Discovery session ID.
            intake_request_ids: Mapping of candidate_id -> intake_request_id.

        Returns:
            Summary of completed handoffs.
        """
        # Would update candidates with intake_request_id
        # and mark session as completed
        return {
            "status": "completed",
            "handoffs": len(intake_request_ids),
        }

    async def submit_to_intake(
        self,
        session_id: UUID,
        request: HandoffRequest,
    ) -> Optional[HandoffResponse]:
        """Submit candidates to the intake system."""
        bundle = await self.create_handoff_bundle(session_id)
        if "error" in bundle:
            return None

        # Would integrate with intake API here
        return HandoffResponse(
            intake_request_id=session_id,  # placeholder
            status="submitted",
            candidates_count=bundle["count"],
        )

    async def validate_readiness(
        self,
        session_id: UUID,
    ) -> Optional[ValidationResult]:
        """Validate whether the session is ready for handoff."""
        all_candidates = await self.candidate_repository.get_for_session(session_id)
        selected = [c for c in all_candidates if c.selected_for_build]

        warnings = []
        errors = []

        if not selected:
            errors.append("No candidates selected for build")
        elif len(selected) > 10:
            warnings.append("Large number of candidates may take longer to process")

        return ValidationResult(
            is_ready=len(errors) == 0,
            warnings=warnings,
            errors=errors,
        )

    async def get_status(
        self,
        session_id: UUID,
    ) -> Optional[HandoffStatus]:
        """Get the handoff status for a session."""
        all_candidates = await self.candidate_repository.get_for_session(session_id)
        selected = [c for c in all_candidates if c.selected_for_build]

        return HandoffStatus(
            handed_off=len(selected) > 0,
            intake_request_id=None,
            candidates_count=len(selected),
        )


def get_handoff_service() -> HandoffService:
    """Dependency placeholder - will be replaced with DI."""
    raise NotImplementedError("Use dependency injection")
