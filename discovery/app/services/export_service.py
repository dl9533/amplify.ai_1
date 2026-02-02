# discovery/app/services/export_service.py
"""Export service for generating reports."""
from typing import Any, Optional
from uuid import UUID

from app.repositories.session_repository import SessionRepository
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.candidate_repository import CandidateRepository


class ExportService:
    """Service for exporting discovery results."""

    def __init__(
        self,
        session_repository: SessionRepository,
        analysis_repository: AnalysisRepository | None = None,
        candidate_repository: CandidateRepository | None = None,
    ) -> None:
        self.session_repository = session_repository
        self.analysis_repository = analysis_repository
        self.candidate_repository = candidate_repository

    async def export_json(self, session_id: UUID) -> dict[str, Any]:
        """Export session data as JSON."""
        session = await self.session_repository.get_by_id(session_id)
        if not session:
            return {"error": "Session not found"}

        result: dict[str, Any] = {
            "session_id": str(session.id),
            "created_at": session.created_at.isoformat(),
            "status": session.status.value,
            "analysis_results": [],
            "candidates": [],
        }

        if self.analysis_repository:
            results = await self.analysis_repository.get_for_session(session_id)
            result["analysis_results"] = [
                {
                    "dimension": r.dimension.value,
                    "name": r.dimension_value,
                    "ai_exposure": r.ai_exposure_score,
                    "impact": r.impact_score,
                    "priority": r.priority_score,
                }
                for r in results
            ]

        if self.candidate_repository:
            candidates = await self.candidate_repository.get_for_session(session_id)
            result["candidates"] = [
                {
                    "name": c.name,
                    "priority_tier": c.priority_tier.value,
                    "estimated_impact": c.estimated_impact,
                    "selected_for_build": c.selected_for_build,
                }
                for c in candidates
            ]

        return result

    async def export_csv(self, session_id: UUID) -> str:
        """Export analysis results as CSV."""
        if not self.analysis_repository:
            return "dimension,name,ai_exposure,impact,priority\n"

        results = await self.analysis_repository.get_for_session(session_id)
        lines = ["dimension,name,ai_exposure,impact,priority"]

        for r in results:
            lines.append(
                f"{r.dimension.value},{r.dimension_value},"
                f"{r.ai_exposure_score},{r.impact_score},{r.priority_score}"
            )

        return "\n".join(lines)

    async def generate_csv(
        self,
        session_id: UUID,
        dimension: Optional[str] = None,
    ) -> Optional[bytes]:
        """Generate CSV export of analysis results."""
        csv_content = await self.export_csv(session_id)
        return csv_content.encode("utf-8")

    async def generate_xlsx(
        self,
        session_id: UUID,
    ) -> Optional[bytes]:
        """Generate Excel export of analysis results."""
        # Would use openpyxl to generate actual Excel file
        # For now, return CSV-like content
        csv_content = await self.export_csv(session_id)
        return csv_content.encode("utf-8")

    async def generate_pdf(
        self,
        session_id: UUID,
    ) -> Optional[bytes]:
        """Generate PDF report of analysis results."""
        # Would use a PDF library to generate actual PDF
        # For now, return placeholder
        json_content = await self.export_json(session_id)
        return str(json_content).encode("utf-8")

    async def generate_handoff_bundle(
        self,
        session_id: UUID,
    ) -> Optional[dict[str, Any]]:
        """Generate handoff bundle with all session data."""
        return await self.export_json(session_id)


from collections.abc import AsyncGenerator


async def get_export_service() -> AsyncGenerator[ExportService, None]:
    """Get export service dependency for FastAPI.

    Yields a fully configured ExportService with all repositories.
    """
    from app.models.base import async_session_maker

    async with async_session_maker() as db:
        session_repository = SessionRepository(db)
        analysis_repository = AnalysisRepository(db)
        candidate_repository = CandidateRepository(db)
        service = ExportService(
            session_repository=session_repository,
            analysis_repository=analysis_repository,
            candidate_repository=candidate_repository,
        )
        yield service
