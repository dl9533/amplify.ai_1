"""LOB mappings router for the Discovery module."""
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, Query, status

from app.schemas.lob_mapping import LobNaicsLookupResponse
from app.services.lob_mapping_service import LobMappingService, LobNaicsResult


router = APIRouter(
    prefix="/discovery",
    tags=["discovery-lob-mappings"],
)


async def get_lob_mapping_service() -> AsyncGenerator[LobMappingService, None]:
    """Get LOB mapping service dependency for FastAPI.

    Yields a LobMappingService configured with the repository.
    """
    from app.models.base import async_session_maker
    from app.repositories.lob_mapping_repository import LobMappingRepository

    async with async_session_maker() as db:
        repository = LobMappingRepository(db)
        yield LobMappingService(repository=repository)


@router.get(
    "/lob/lookup",
    response_model=LobNaicsLookupResponse,
    status_code=status.HTTP_200_OK,
    summary="Lookup NAICS codes for a Line of Business",
    description="Maps a Line of Business string to NAICS industry codes using curated mappings, fuzzy matching, or LLM fallback.",
)
async def lookup_lob(
    lob: str = Query(
        ...,
        min_length=1,
        description="Line of Business to lookup",
    ),
    service: LobMappingService = Depends(get_lob_mapping_service),
) -> LobNaicsLookupResponse:
    """Lookup NAICS codes for a Line of Business.

    Returns the mapped NAICS codes with confidence score and source.
    """
    result: LobNaicsResult = await service.map_lob_to_naics(lob)

    return LobNaicsLookupResponse(
        lob=result.lob,
        naics_codes=result.naics_codes,
        confidence=result.confidence,
        source=result.source,
    )
