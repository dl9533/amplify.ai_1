"""Exports router for the Discovery module."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response

from app.schemas.export import HandoffBundle
from app.services.export_service import (
    ExportService,
    get_export_service,
)


router = APIRouter(
    prefix="/discovery",
    tags=["discovery-exports"],
)


@router.get(
    "/sessions/{session_id}/export/csv",
    status_code=status.HTTP_200_OK,
    summary="Export analysis as CSV",
    description="Export analysis results as a CSV file with optional dimension filter.",
)
async def export_csv(
    session_id: UUID,
    dimension: Optional[str] = Query(
        None,
        description="Filter by dimension (ROLE, DEPARTMENT, etc.)",
    ),
    service: ExportService = Depends(get_export_service),
) -> Response:
    """Export analysis results as CSV."""
    content = await service.generate_csv(session_id, dimension)

    if content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID {session_id} not found",
        )

    return Response(
        content=content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=export_{session_id}.csv"
        },
    )


@router.get(
    "/sessions/{session_id}/export/xlsx",
    status_code=status.HTTP_200_OK,
    summary="Export analysis as Excel",
    description="Export analysis results as an Excel spreadsheet.",
)
async def export_xlsx(
    session_id: UUID,
    service: ExportService = Depends(get_export_service),
) -> Response:
    """Export analysis results as Excel file."""
    content = await service.generate_xlsx(session_id)

    if content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID {session_id} not found",
        )

    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=export_{session_id}.xlsx"
        },
    )


@router.get(
    "/sessions/{session_id}/export/pdf",
    status_code=status.HTTP_200_OK,
    summary="Export analysis as PDF",
    description="Export analysis results as a PDF report.",
)
async def export_pdf(
    session_id: UUID,
    service: ExportService = Depends(get_export_service),
) -> Response:
    """Export analysis results as PDF report."""
    content = await service.generate_pdf(session_id)

    if content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID {session_id} not found",
        )

    return Response(
        content=content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=report_{session_id}.pdf"
        },
    )


@router.get(
    "/sessions/{session_id}/export/handoff",
    response_model=HandoffBundle,
    status_code=status.HTTP_200_OK,
    summary="Export handoff bundle",
    description="Export full handoff bundle as JSON with session summary, role mappings, analysis results, and roadmap.",
)
async def export_handoff(
    session_id: UUID,
    service: ExportService = Depends(get_export_service),
) -> HandoffBundle:
    """Export full handoff bundle as JSON."""
    result = await service.generate_handoff_bundle(session_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID {session_id} not found",
        )

    return HandoffBundle(
        session_summary=result["session_summary"],
        role_mappings=result["role_mappings"],
        analysis_results=result["analysis_results"],
        roadmap=result["roadmap"],
    )
