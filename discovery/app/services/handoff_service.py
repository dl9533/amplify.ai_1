# discovery/app/services/handoff_service.py
"""Handoff service for Build intake integration."""
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

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
        # In-memory tracking of handoffs (would be DB in production)
        self._handoff_records: dict[UUID, dict[str, Any]] = {}

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
        # Update handoff record
        if session_id in self._handoff_records:
            self._handoff_records[session_id]["status"] = "completed"
            self._handoff_records[session_id]["intake_request_ids"] = intake_request_ids
            self._handoff_records[session_id]["completed_at"] = datetime.now(timezone.utc).isoformat()

        return {
            "status": "completed",
            "handoffs": len(intake_request_ids),
        }

    async def submit_to_intake(
        self,
        session_id: UUID,
        request: HandoffRequest,
    ) -> Optional[HandoffResponse]:
        """Submit candidates to the intake system.

        In production, this would call the Build intake API.
        Currently generates a tracking ID and stores handoff metadata.
        """
        bundle = await self.create_handoff_bundle(session_id)
        if "error" in bundle:
            return None

        # Generate a unique intake request ID
        intake_request_id = uuid4()

        # Store handoff record for tracking
        self._handoff_records[session_id] = {
            "intake_request_id": intake_request_id,
            "session_id": session_id,
            "status": "submitted",
            "candidates_count": bundle["count"],
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "notes": request.notes if request else None,
            "candidate_ids": request.candidate_ids if request else None,
        }

        return HandoffResponse(
            intake_request_id=intake_request_id,
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

        # Check for candidates without descriptions
        missing_desc = [c for c in selected if not c.description]
        if missing_desc:
            warnings.append(f"{len(missing_desc)} candidates are missing descriptions")

        # Check for already handed-off session
        if session_id in self._handoff_records:
            existing = self._handoff_records[session_id]
            if existing.get("status") == "completed":
                errors.append("Session has already been handed off")
            elif existing.get("status") == "submitted":
                warnings.append("A handoff is already in progress for this session")

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
        # Check if we have a handoff record
        if session_id in self._handoff_records:
            record = self._handoff_records[session_id]
            return HandoffStatus(
                session_id=session_id,
                handed_off=record.get("status") in ("submitted", "completed"),
                intake_request_id=record.get("intake_request_id"),
                handed_off_at=record.get("submitted_at"),
            )

        # No handoff yet
        return HandoffStatus(
            session_id=session_id,
            handed_off=False,
            intake_request_id=None,
            handed_off_at=None,
        )


from collections.abc import AsyncGenerator


async def get_handoff_service() -> AsyncGenerator[HandoffService, None]:
    """Get handoff service dependency for FastAPI.

    Yields a fully configured HandoffService with repositories.
    """
    from app.models.base import async_session_maker

    async with async_session_maker() as db:
        candidate_repository = CandidateRepository(db)
        session_repository = SessionRepository(db)
        service = HandoffService(
            candidate_repository=candidate_repository,
            session_repository=session_repository,
        )
        yield service
