"""Role mapping service for managing role-to-O*NET mappings.

Uses LLM-powered semantic mapping via RoleMappingAgent.
"""
import logging
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID

from app.config import get_settings
from app.repositories.onet_repository import OnetRepository
from app.repositories.role_mapping_repository import RoleMappingRepository
from app.services.file_parser import FileParser
from app.services.upload_service import UploadService

if TYPE_CHECKING:
    from app.agents.role_mapping_agent import RoleMappingAgent

logger = logging.getLogger(__name__)


class RoleMappingService:
    """Service for role-to-O*NET occupation mapping.

    Uses LLM-powered RoleMappingAgent for semantic role matching.

    Attributes:
        repository: Repository for role mapping persistence.
        upload_service: Service for file uploads.
        role_mapping_agent: LLM-powered mapping agent.
    """

    def __init__(
        self,
        repository: RoleMappingRepository,
        role_mapping_agent: "RoleMappingAgent",
        upload_service: UploadService | None = None,
    ) -> None:
        """Initialize the role mapping service.

        Args:
            repository: Repository for role mapping persistence.
            role_mapping_agent: LLM-powered mapping agent.
            upload_service: Service for file uploads.
        """
        self.repository = repository
        self.role_mapping_agent = role_mapping_agent
        self.upload_service = upload_service
        self._file_parser = FileParser()

    async def create_mappings_from_upload(
        self,
        session_id: UUID,
        upload_id: UUID,
        role_column: str,
    ) -> list[dict[str, Any]]:
        """Create role mappings from uploaded file.

        Uses the LLM-powered agent for semantic role matching.

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

        logger.info(f"Using LLM agent to map {len(role_names)} roles")

        # Call agent to map all roles
        results = await self.role_mapping_agent.map_roles(role_names)

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
                "is_confirmed": mapping.user_confirmed,
            })

        return mappings

    async def map_roles(self, role_names: list[str]) -> list[dict[str, Any]]:
        """Map a list of role names to O*NET occupations.

        Args:
            role_names: List of role titles to map.

        Returns:
            List of mapping result dicts with onet_code, onet_title,
            confidence_score, confidence_tier, and reasoning.
        """
        results = await self.role_mapping_agent.map_roles(role_names)
        return [
            {
                "source_role": r.source_role,
                "onet_code": r.onet_code,
                "onet_title": r.onet_title,
                "confidence_score": r.confidence_score,
                "confidence_tier": r.confidence.value,
                "reasoning": r.reasoning,
            }
            for r in results
        ]

    async def get_by_session_id(self, session_id: UUID) -> list[dict[str, Any]]:
        """Get all mappings for a session."""
        mappings = await self.repository.get_for_session(session_id)
        return [
            {
                "id": str(m.id),
                "source_role": m.source_role,
                "onet_code": m.onet_code,
                "onet_title": getattr(m, "onet_title", None),
                "confidence_score": m.confidence_score,
                "row_count": m.row_count,
                "is_confirmed": m.user_confirmed,
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
            "onet_title": onet_title,
            "is_confirmed": mapping.user_confirmed,
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
            "is_confirmed": mapping.user_confirmed,
        }

    async def bulk_confirm(
        self,
        session_id: UUID,
        threshold: float = 0.85,
    ) -> dict[str, Any]:
        """Bulk confirm mappings above confidence threshold."""
        mappings = await self.repository.get_for_session(session_id)
        confirmed = 0

        for mapping in mappings:
            if (
                not mapping.user_confirmed
                and mapping.onet_code
                and mapping.confidence_score >= threshold
            ):
                await self.repository.confirm(mapping.id, mapping.onet_code)
                confirmed += 1

        return {"confirmed_count": confirmed}


class OnetService:
    """O*NET service for searching and retrieving occupation data.

    Uses the local O*NET repository for data access.

    Attributes:
        repository: OnetRepository for database access.
    """

    def __init__(self, repository: OnetRepository) -> None:
        """Initialize the O*NET service.

        Args:
            repository: OnetRepository instance for database access.
        """
        self.repository = repository

    async def search(self, query: str) -> list[dict]:
        """Search O*NET occupations by query.

        Args:
            query: Search query string.

        Returns:
            List of matching occupations with code, title, and score.
        """
        occupations = await self.repository.search_with_full_text(query)
        return [
            {
                "code": occ.code,
                "title": occ.title,
                "score": 1.0,  # Full-text search doesn't return scores
            }
            for occ in occupations
        ]

    async def get_occupation(self, code: str) -> Optional[dict]:
        """Get O*NET occupation details by code.

        Args:
            code: O*NET SOC code.

        Returns:
            Occupation details dictionary, or None if not found.
        """
        occupation = await self.repository.get_by_code(code)
        if not occupation:
            return None
        return {
            "code": occupation.code,
            "title": occupation.title,
            "description": occupation.description,
        }


async def get_role_mapping_service() -> AsyncGenerator[RoleMappingService, None]:
    """Get role mapping service dependency for FastAPI.

    Yields a fully configured RoleMappingService with the LLM-powered
    RoleMappingAgent for semantic role matching.
    """
    from app.agents.role_mapping_agent import RoleMappingAgent
    from app.models.base import async_session_maker
    from app.services.llm_service import get_llm_service

    settings = get_settings()

    async with async_session_maker() as db:
        repository = RoleMappingRepository(db)
        onet_repo = OnetRepository(db)

        # Get LLM service
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


async def get_onet_service() -> AsyncGenerator[OnetService, None]:
    """Get O*NET service dependency for FastAPI.

    Yields an OnetService configured with the local repository.
    """
    from app.models.base import async_session_maker

    async with async_session_maker() as db:
        repository = OnetRepository(db)
        yield OnetService(repository=repository)
