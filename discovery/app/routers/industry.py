"""Industry reference data router."""
from fastapi import APIRouter, status

from app.data.industry_sectors import SUPERSECTORS
from app.schemas.industry import (
    IndustryListResponse,
    SupersectorResponse,
    NaicsSectorResponse,
)


router = APIRouter(
    prefix="/discovery/industries",
    tags=["discovery-industries"],
)


@router.get(
    "",
    response_model=IndustryListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all industries",
    description="Returns all BLS supersectors with their NAICS sectors for industry selection.",
)
async def list_industries() -> IndustryListResponse:
    """List all available industries organized by BLS supersector."""
    supersectors = [
        SupersectorResponse(
            code=ss["code"],
            label=ss["label"],
            sectors=[
                NaicsSectorResponse(code=s["code"], label=s["label"])
                for s in ss["sectors"]
            ],
        )
        for ss in SUPERSECTORS
    ]

    return IndustryListResponse(supersectors=supersectors)
