"""O*NET API client for occupation data retrieval.

This module provides an async client for interacting with the O*NET Web Services API
to retrieve occupation data, tasks, and work activities.

O*NET Web Services API v2:
- Base URL: https://api-v2.onetcenter.org/
- Authentication: X-API-Key header
- Returns JSON
"""

import logging
from typing import Any

import httpx

from app.config import Settings
from app.exceptions import (
    OnetApiError,
    OnetAuthError,
    OnetNotFoundError,
    OnetRateLimitError,
)

logger = logging.getLogger(__name__)


class OnetApiClient:
    """Async client for O*NET Web Services API.

    Provides methods to search occupations and retrieve occupation details,
    tasks, and work activities.

    Attributes:
        settings: Application settings containing API configuration.
        base_url: The base URL for O*NET Web Services.
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize the O*NET API client.

        Args:
            settings: Application settings with onet_api_key and onet_api_base_url.
        """
        self.settings = settings
        self.base_url = settings.onet_api_base_url

    def _get_api_key(self) -> str:
        """Get the API key from settings.

        Returns:
            The O*NET API key as a string.
        """
        return self.settings.onet_api_key.get_secret_value()

    def _get_headers(self) -> dict[str, str]:
        """Create headers for O*NET API v2 requests.

        O*NET v2 uses X-API-Key header for authentication.

        Returns:
            Dict with Accept and X-API-Key headers.
        """
        return {
            "Accept": "application/json",
            "X-API-Key": self._get_api_key(),
        }

    async def _get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a GET request to the O*NET API.

        Args:
            endpoint: API endpoint path (relative to base_url).
            params: Optional query parameters.

        Returns:
            JSON response as a dictionary.

        Raises:
            OnetRateLimitError: If rate limit is exceeded (429).
            OnetAuthError: If authentication fails (401).
            OnetNotFoundError: If the resource is not found (404).
            OnetApiError: For other HTTP errors.
        """
        url = f"{self.base_url}{endpoint}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                url=url,
                headers=self._get_headers(),
                params=params,
            )

            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code
                if status_code == 429:
                    retry_after = e.response.headers.get("Retry-After")
                    retry_seconds: int | None = None
                    if retry_after:
                        try:
                            retry_seconds = int(retry_after)
                        except ValueError:
                            logger.warning(f"Invalid Retry-After header: {retry_after}")
                            retry_seconds = None
                    raise OnetRateLimitError(
                        message="O*NET API rate limit exceeded",
                        retry_after=retry_seconds,
                    ) from e
                elif status_code == 401:
                    raise OnetAuthError(
                        message="O*NET API authentication failed",
                    ) from e
                elif status_code in (404, 422):
                    # 404 = not found, 422 = invalid code format (v2 API)
                    raise OnetNotFoundError(
                        message=f"O*NET resource not found: {endpoint}",
                        resource=endpoint,
                    ) from e
                else:
                    raise OnetApiError(
                        message=f"O*NET API error: {e}",
                        status_code=status_code,
                    ) from e

            return response.json()

    async def search_occupations(self, keyword: str) -> list[dict[str, Any]]:
        """Search O*NET occupations by keyword.

        Args:
            keyword: Search term to match against occupation titles.

        Returns:
            List of occupation dictionaries with 'code' and 'title' fields.
        """
        response = await self._get("mnm/search", params={"keyword": keyword})
        # v2 API uses 'career' key instead of 'occupation'
        return response.get("career", [])

    async def get_occupation(self, code: str) -> dict[str, Any] | None:
        """Get occupation details by O*NET code.

        Args:
            code: O*NET occupation code (e.g., "15-1252.00").

        Returns:
            Dictionary with occupation details, or None if not found.
        """
        try:
            return await self._get(f"online/occupations/{code}")
        except OnetNotFoundError:
            return None

    async def get_work_activities(self, code: str) -> list[dict[str, Any]]:
        """Get work activities (GWAs/DWAs) for an occupation.

        Work activities describe general types of job behaviors.

        Args:
            code: O*NET occupation code (e.g., "15-1252.00").

        Returns:
            List of work activity dictionaries with 'id' and 'name' fields.
        """
        response = await self._get(f"online/occupations/{code}/summary/work_activities")
        return response.get("element", [])

    async def get_tasks(self, code: str) -> list[dict[str, Any]]:
        """Get tasks for an occupation.

        Args:
            code: O*NET occupation code (e.g., "15-1252.00").

        Returns:
            List of task dictionaries with 'id' and 'statement' fields.
        """
        response = await self._get(f"online/occupations/{code}/summary/tasks")
        return response.get("task", [])
