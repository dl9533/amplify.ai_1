"""Role mapping service for managing role-to-O*NET mappings.

Supports both LLM-powered agent mapping and legacy fuzzy matching.
"""
import logging
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any, List, Optional
from uuid import UUID

if TYPE_CHECKING:
    from app.agents.role_mapping_agent import RoleMappingAgent

from app.config import get_settings
from app.repositories.role_mapping_repository import RoleMappingRepository
from app.services.onet_client import OnetApiClient
from app.services.upload_service import UploadService
from app.services.fuzzy_matcher import FuzzyMatcher
from app.services.file_parser import FileParser

logger = logging.getLogger(__name__)


class RoleMappingService:
    """Service for role-to-O*NET occupation mapping.

    Supports two mapping strategies:
    1. LLM-powered RoleMappingAgent (preferred when available)
    2. Fuzzy string matching (fallback/legacy)

    Attributes:
        repository: Repository for role mapping persistence.
        onet_client: Client for O*NET API calls (used with fuzzy matcher).
        upload_service: Service for file uploads.
        fuzzy_matcher: Legacy fuzzy string matcher.
        role_mapping_agent: LLM-powered mapping agent.
    """

    def __init__(
        self,
        repository: RoleMappingRepository,
        onet_client: OnetApiClient | None = None,
        upload_service: UploadService | None = None,
        fuzzy_matcher: FuzzyMatcher | None = None,
        role_mapping_agent: "RoleMappingAgent | None" = None,
    ) -> None:
        """Initialize the role mapping service.

        Args:
            repository: Repository for role mapping persistence.
            onet_client: Client for O*NET API calls (used with fuzzy matcher).
            upload_service: Service for file uploads.
            fuzzy_matcher: Legacy fuzzy string matcher.
            role_mapping_agent: LLM-powered mapping agent (preferred).
        """
        self.repository = repository
        self.onet_client = onet_client
        self.upload_service = upload_service
        self.fuzzy_matcher = fuzzy_matcher or FuzzyMatcher()
        self.role_mapping_agent = role_mapping_agent
        self._file_parser = FileParser()

    async def create_mappings_from_upload(
        self,
        session_id: UUID,
        upload_id: UUID,
        role_column: str,
    ) -> list[dict[str, Any]]:
        """Create role mappings from uploaded file.

        Uses the LLM-powered agent if available, otherwise falls back
        to fuzzy string matching.

        Args:
            session_id: Discovery session ID.
            upload_id: Upload ID containing the file.
            role_column: Column name containing roles.

        Returns:
            List of created mapping dicts.
        """
        if not self.upload_service:
            raise ValueError("upload_service required")

        # Get file content
        content = await self.upload_service.get_file_content(upload_id)
        if not content:
            return []

        # Extract unique roles
        upload = await self.upload_service.repository.get_by_id(upload_id)
        unique_roles = self._file_parser.extract_unique_values(
            content, upload.file_name, role_column
        )

        if not unique_roles:
            return []

        # Get role names and their counts
        role_names = [r["value"] for r in unique_roles]
        role_counts = {r["value"]: r["count"] for r in unique_roles}

        # Use agent if available, otherwise fall back to fuzzy matching
        if self.role_mapping_agent:
            logger.info(f"Using LLM agent to map {len(role_names)} roles")
            return await self._create_mappings_with_agent(
                session_id, role_names, role_counts
            )
        else:
            logger.info(f"Using fuzzy matcher to map {len(role_names)} roles")
            return await self._create_mappings_with_fuzzy(
                session_id, role_names, role_counts
            )

    async def _create_mappings_with_agent(
        self,
        session_id: UUID,
        role_names: list[str],
        role_counts: dict[str, int],
    ) -> list[dict[str, Any]]:
        """Create mappings using the LLM-powered agent.

        Args:
            session_id: Discovery session ID.
            role_names: List of role names to map.
            role_counts: Dict mapping role name to row count.

        Returns:
            List of created mapping dicts.
        """
        # Import here to avoid circular dependency
        from app.agents.role_mapping_agent import RoleMappingResult

        # Call agent to map all roles
        results: list[RoleMappingResult] = await self.role_mapping_agent.map_roles(
            role_names
        )

        # Create mapping records
        mappings = []
        for result in results:
            mapping = await self.repository.create(
                session_id=session_id,
                source_role=result.source_role,
                onet_code=result.onet_code,
                confidence_score=result.confidence_score,
                row_count=role_counts.get(result.source_role, 1),
            )

            mappings.append({
                "id": str(mapping.id),
                "source_role": mapping.source_role,
                "onet_code": mapping.onet_code,
                "onet_title": result.onet_title,
                "confidence_score": mapping.confidence_score,
                "confidence_tier": result.confidence.value,
                "reasoning": result.reasoning,
                "row_count": mapping.row_count,
                "user_confirmed": mapping.user_confirmed,
            })

        return mappings

    async def _create_mappings_with_fuzzy(
        self,
        session_id: UUID,
        role_names: list[str],
        role_counts: dict[str, int],
    ) -> list[dict[str, Any]]:
        """Create mappings using fuzzy string matching (legacy).

        Args:
            session_id: Discovery session ID.
            role_names: List of role names to map.
            role_counts: Dict mapping role name to row count.

        Returns:
            List of created mapping dicts.
        """
        if not self.onet_client:
            raise ValueError("onet_client required for fuzzy matching")

        mappings = []

        for role_name in role_names:
            row_count = role_counts.get(role_name, 1)

            # Search O*NET for matches
            search_results = await self.onet_client.search_occupations(role_name)

            # Find best match using fuzzy matching
            if search_results:
                best_matches = self.fuzzy_matcher.find_best_matches(
                    role_name, search_results, top_n=1
                )
                if best_matches:
                    best = best_matches[0]
                    onet_code = best.get("code")
                    confidence = best.get("score", 0.0)
                else:
                    onet_code = None
                    confidence = 0.0
            else:
                onet_code = None
                confidence = 0.0

            # Create mapping record
            mapping = await self.repository.create(
                session_id=session_id,
                source_role=role_name,
                onet_code=onet_code,
                confidence_score=confidence,
                row_count=row_count,
            )

            mappings.append({
                "id": str(mapping.id),
                "source_role": mapping.source_role,
                "onet_code": mapping.onet_code,
                "confidence_score": mapping.confidence_score,
                "row_count": mapping.row_count,
                "user_confirmed": mapping.user_confirmed,
            })

        return mappings

    async def get_by_session_id(self, session_id: UUID) -> list[dict[str, Any]]:
        """Get all mappings for a session."""
        mappings = await self.repository.get_for_session(session_id)
        return [
            {
                "id": str(m.id),
                "source_role": m.source_role,
                "onet_code": m.onet_code,
                "confidence_score": m.confidence_score,
                "row_count": m.row_count,
                "user_confirmed": m.user_confirmed,
            }
            for m in mappings
        ]

    async def update(
        self,
        mapping_id: UUID,
        onet_code: Optional[str] = None,
        onet_title: Optional[str] = None,
        is_confirmed: Optional[bool] = None,
    ) -> Optional[dict]:
        """Update a role mapping.

        Args:
            mapping_id: The mapping ID to update.
            onet_code: New O*NET code (optional).
            onet_title: New O*NET title (optional).
            is_confirmed: New confirmation status (optional).

        Returns:
            Updated role mapping dictionary, or None if not found.
        """
        mapping = await self.repository.update(
            mapping_id, onet_code=onet_code, user_confirmed=is_confirmed
        )
        if not mapping:
            return None
        return {
            "id": str(mapping.id),
            "source_role": mapping.source_role,
            "onet_code": mapping.onet_code,
            "user_confirmed": mapping.user_confirmed,
        }

    async def confirm_mapping(
        self,
        mapping_id: UUID,
        onet_code: str,
    ) -> dict[str, Any] | None:
        """Confirm a mapping with selected O*NET code."""
        mapping = await self.repository.confirm(mapping_id, onet_code)
        if not mapping:
            return None
        return {
            "id": str(mapping.id),
            "source_role": mapping.source_role,
            "onet_code": mapping.onet_code,
            "user_confirmed": mapping.user_confirmed,
        }

    async def bulk_confirm(
        self,
        session_id: UUID,
        min_confidence: float = 0.85,
    ) -> dict[str, Any]:
        """Bulk confirm mappings above confidence threshold."""
        mappings = await self.repository.get_for_session(session_id)
        confirmed = 0

        for mapping in mappings:
            if (
                not mapping.user_confirmed
                and mapping.onet_code
                and mapping.confidence_score >= min_confidence
            ):
                await self.repository.confirm(mapping.id, mapping.onet_code)
                confirmed += 1

        return {"confirmed_count": confirmed}

    async def search_occupations(self, query: str) -> list[dict[str, Any]]:
        """Search O*NET occupations for manual mapping."""
        if not self.onet_client:
            return []
        return await self.onet_client.search_occupations(query)


class OnetService:
    """O*NET service for searching and retrieving occupation data.

    This service wraps the OnetApiClient to provide a clean interface
    for searching and retrieving O*NET occupation data.

    Attributes:
        client: The OnetApiClient instance for making API calls.
    """

    def __init__(self, client: OnetApiClient) -> None:
        """Initialize the O*NET service.

        Args:
            client: OnetApiClient instance for API communication.
        """
        self.client = client

    async def search(self, query: str) -> List[dict]:
        """Search O*NET occupations by query.

        Args:
            query: Search query string.

        Returns:
            List of matching occupations with code, title, and score.
        """
        return await self.client.search_occupations(query)

    async def get_occupation(self, code: str) -> Optional[dict]:
        """Get O*NET occupation details by code.

        Args:
            code: O*NET SOC code.

        Returns:
            Occupation details dictionary, or None if not found.
        """
        return await self.client.get_occupation(code)


async def get_role_mapping_service() -> AsyncGenerator[RoleMappingService, None]:
    """Get role mapping service dependency for FastAPI.

    Yields a fully configured RoleMappingService with repository, O*NET client,
    and fuzzy matcher (legacy mode).
    """
    from app.models.base import async_session_maker
    from app.repositories.role_mapping_repository import RoleMappingRepository

    settings = get_settings()
    onet_client = OnetApiClient(settings=settings)
    fuzzy_matcher = FuzzyMatcher()

    async with async_session_maker() as db:
        repository = RoleMappingRepository(db)
        service = RoleMappingService(
            repository=repository,
            onet_client=onet_client,
            fuzzy_matcher=fuzzy_matcher,
        )
        yield service


async def get_role_mapping_service_with_agent() -> AsyncGenerator[RoleMappingService, None]:
    """Get role mapping service with LLM agent for FastAPI.

    Yields a fully configured RoleMappingService with the LLM-powered
    RoleMappingAgent for semantic role matching.
    """
    from app.models.base import async_session_maker
    from app.repositories.role_mapping_repository import RoleMappingRepository
    from app.repositories.onet_repository import OnetRepository
    from app.agents.role_mapping_agent import RoleMappingAgent
    from app.services.llm_service import get_llm_service

    settings = get_settings()

    async with async_session_maker() as db:
        repository = RoleMappingRepository(db)
        onet_repo = OnetRepository(db)

        # Get LLM service (synchronous function, takes settings)
        llm_service = get_llm_service(settings)

        # Create role mapping agent
        agent = RoleMappingAgent(
            llm_service=llm_service,
            onet_repository=onet_repo,
        )

        service = RoleMappingService(
            repository=repository,
            role_mapping_agent=agent,
        )
        yield service


def get_onet_service() -> OnetService:
    """Dependency to get O*NET service.

    Creates an OnetApiClient with application settings and injects it
    into a new OnetService instance.

    Returns:
        OnetService instance configured with API client.
    """
    settings = get_settings()
    client = OnetApiClient(settings=settings)
    return OnetService(client=client)
