"""Role mapping service for managing role-to-O*NET mappings."""
from typing import List, Optional
from uuid import UUID

from app.config import get_settings
from app.services.onet_client import OnetApiClient


class RoleMappingService:
    """Role mapping service for managing role-to-O*NET mappings.

    This is a placeholder service that will be replaced with actual
    database operations in a later task.
    """

    async def get_by_session_id(self, session_id: UUID) -> List[dict]:
        """Get all role mappings for a session.

        Args:
            session_id: The session ID to get mappings for.

        Returns:
            List of role mapping dictionaries.
        """
        raise NotImplementedError("Service not implemented")

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
        raise NotImplementedError("Service not implemented")

    async def bulk_confirm(
        self,
        session_id: UUID,
        threshold: float,
    ) -> dict:
        """Bulk confirm mappings above a confidence threshold.

        Args:
            session_id: The session ID to confirm mappings for.
            threshold: Minimum confidence score for auto-confirmation.

        Returns:
            Dictionary with confirmed_count.
        """
        raise NotImplementedError("Service not implemented")


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


def get_role_mapping_service() -> RoleMappingService:
    """Dependency to get role mapping service."""
    return RoleMappingService()


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
