"""Handoff services for the Discovery module."""
from typing import Optional
from uuid import UUID

from app.schemas.handoff import (
    HandoffRequest,
    HandoffResponse,
    HandoffStatus,
    ValidationResult,
)


class HandoffService:
    """Handoff service for submitting discovery results to intake.

    This is a placeholder service that will be replaced with actual
    implementation in a later task.
    """

    async def submit_to_intake(
        self,
        session_id: UUID,
        request: HandoffRequest,
    ) -> Optional[HandoffResponse]:
        """Submit candidates to the intake system.

        Args:
            session_id: The session ID to submit candidates from.
            request: The handoff request with candidate_ids or priority_tier.

        Returns:
            HandoffResponse with intake_request_id and status,
            or None if session not found.

        Raises:
            NotImplementedError: Service not implemented.
        """
        raise NotImplementedError("Service not implemented")

    async def validate_readiness(
        self,
        session_id: UUID,
    ) -> Optional[ValidationResult]:
        """Validate whether the session is ready for handoff.

        Args:
            session_id: The session ID to validate.

        Returns:
            ValidationResult with is_ready status and any warnings/errors,
            or None if session not found.

        Raises:
            NotImplementedError: Service not implemented.
        """
        raise NotImplementedError("Service not implemented")

    async def get_status(
        self,
        session_id: UUID,
    ) -> Optional[HandoffStatus]:
        """Get the handoff status for a session.

        Args:
            session_id: The session ID to get status for.

        Returns:
            HandoffStatus with handed_off status and details,
            or None if session not found.

        Raises:
            NotImplementedError: Service not implemented.
        """
        raise NotImplementedError("Service not implemented")


def get_handoff_service() -> HandoffService:
    """Dependency to get handoff service."""
    return HandoffService()
