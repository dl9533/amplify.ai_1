"""O*NET API client for occupation data retrieval.

This module provides an async client for interacting with the O*NET Web Services API
to retrieve occupation data, tasks, skills, and work activities.

O*NET Web Services API:
- Base URL: https://services.onetcenter.org/ws/
- Authentication: Basic Auth (API key as username, empty password)
- Rate limit: 10 requests/second
- Returns JSON
"""

import asyncio
import logging
import time
from typing import Any

import httpx

from app.modules.discovery.exceptions import (
    OnetApiError,
    OnetNotFoundError,
    OnetRateLimitError,
)

logger = logging.getLogger(__name__)


class OnetApiClient:
    """Async client for O*NET Web Services API.

    Provides methods to search occupations and retrieve occupation details,
    tasks, skills, work activities, and technology skills.

    Attributes:
        api_key: The O*NET API key for authentication.
        base_url: The base URL for O*NET Web Services.
        rate_limit: Maximum requests per second (default: 10).
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://services.onetcenter.org/ws/",
        rate_limit: int = 10,
        timeout: float = 30.0,
    ) -> None:
        """Initialize the O*NET API client.

        Args:
            api_key: O*NET API key for Basic Auth (used as username).
            base_url: Base URL for O*NET Web Services API.
            rate_limit: Maximum requests per second.
            timeout: Request timeout in seconds.
        """
        self.api_key = api_key
        self.base_url = base_url
        self.rate_limit = rate_limit
        self.timeout = timeout

        # Rate limiting state
        self._request_times: list[float] = []
        self._lock = asyncio.Lock()

    def _get_auth(self) -> httpx.BasicAuth:
        """Create Basic Auth credentials for O*NET API.

        O*NET uses the API key as the username with an empty password.

        Returns:
            httpx.BasicAuth instance configured for O*NET.
        """
        return httpx.BasicAuth(username=self.api_key, password="")

    async def _wait_for_rate_limit(self) -> None:
        """Wait if necessary to respect rate limits.

        Implements a sliding window rate limiter that ensures
        no more than `rate_limit` requests are made per second.
        """
        async with self._lock:
            now = time.monotonic()

            # Remove request times older than 1 second
            self._request_times = [
                t for t in self._request_times if now - t < 1.0
            ]

            # If at rate limit, wait until oldest request is > 1 second old
            if len(self._request_times) >= self.rate_limit:
                oldest = self._request_times[0]
                wait_time = 1.0 - (now - oldest)
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    # Clean up again after waiting
                    now = time.monotonic()
                    self._request_times = [
                        t for t in self._request_times if now - t < 1.0
                    ]

            # Record this request
            self._request_times.append(time.monotonic())

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
            OnetNotFoundError: If the resource is not found (404).
            OnetApiError: For other HTTP errors.
        """
        await self._wait_for_rate_limit()

        url = f"{self.base_url}{endpoint}"
        headers = {"Accept": "application/json"}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                url,
                auth=self._get_auth(),
                headers=headers,
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
                elif status_code == 404:
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

        Raises:
            ValueError: If keyword is empty or only whitespace.
        """
        if not keyword or not keyword.strip():
            raise ValueError("keyword cannot be empty")
        response = await self._get("mnm/search", params={"keyword": keyword})
        return response.get("occupation", [])

    async def get_occupation_details(self, code: str) -> dict[str, Any]:
        """Get full details for an occupation.

        Args:
            code: O*NET occupation code (e.g., "15-1252.00").

        Returns:
            Dictionary with occupation details including code, title, and description.
        """
        return await self._get(f"online/occupations/{code}")

    async def get_occupation_tasks(self, code: str) -> list[dict[str, Any]]:
        """Get tasks associated with an occupation.

        Args:
            code: O*NET occupation code (e.g., "15-1252.00").

        Returns:
            List of task dictionaries with 'id' and 'statement' fields.
        """
        response = await self._get(f"online/occupations/{code}/tasks")
        return response.get("task", [])

    async def get_work_activities(self, code: str) -> list[dict[str, Any]]:
        """Get work activities for an occupation.

        Work activities describe general types of job behaviors.

        Args:
            code: O*NET occupation code (e.g., "15-1252.00").

        Returns:
            List of work activity dictionaries with 'id' and 'name' fields.
        """
        response = await self._get(f"online/occupations/{code}/activities")
        return response.get("element", [])

    async def get_skills(self, code: str) -> list[dict[str, Any]]:
        """Get skills required for an occupation.

        Args:
            code: O*NET occupation code (e.g., "15-1252.00").

        Returns:
            List of skill dictionaries with 'id' and 'name' fields.
        """
        response = await self._get(f"online/occupations/{code}/skills")
        return response.get("element", [])

    async def get_technology_skills(self, code: str) -> list[dict[str, Any]]:
        """Get technology skills for an occupation.

        Technology skills are specific software, tools, and technologies
        used in the occupation.

        Args:
            code: O*NET occupation code (e.g., "15-1252.00").

        Returns:
            List of technology category dictionaries.
        """
        response = await self._get(f"online/occupations/{code}/technology_skills")
        return response.get("category", [])

    async def get_occupation(self, code: str) -> dict[str, Any]:
        """Get occupation by code.

        Alias for get_occupation_details for convenience.

        Args:
            code: O*NET occupation code (e.g., "15-1252.00").

        Returns:
            Dictionary with occupation details including code, title, and description.

        Raises:
            OnetNotFoundError: If the occupation code is not found.
        """
        return await self._get(f"online/occupations/{code}")

    async def search_occupations_with_retry(
        self,
        keyword: str,
        max_retries: int = 3,
        base_delay: float = 1.0,
    ) -> list[dict[str, Any]]:
        """Search occupations with exponential backoff on rate limit errors.

        Args:
            keyword: Search term to match against occupation titles.
            max_retries: Maximum number of retry attempts (must be >= 1).
            base_delay: Base delay in seconds for exponential backoff (must be >= 0).

        Returns:
            List of occupation dictionaries with 'code' and 'title' fields.

        Raises:
            ValueError: If keyword is empty, max_retries < 1, or base_delay < 0.
            OnetRateLimitError: If rate limit is still exceeded after all retries.
            OnetApiError: For other API errors.
        """
        # Input validation
        if not keyword or not keyword.strip():
            raise ValueError("keyword cannot be empty")
        if max_retries < 1:
            raise ValueError("max_retries must be >= 1")
        if base_delay < 0:
            raise ValueError("base_delay must be non-negative")

        last_error: OnetRateLimitError | None = None

        for attempt in range(max_retries):
            try:
                response = await self._get("mnm/search", params={"keyword": keyword})
                return response.get("occupation", [])
            except OnetRateLimitError as e:
                last_error = e
                if attempt < max_retries - 1:
                    # Exponential backoff: base_delay * 2^attempt
                    delay = base_delay * (2 ** attempt)
                    # Use retry_after from server if available
                    if e.retry_after:
                        delay = max(delay, float(e.retry_after))
                    await asyncio.sleep(delay)

        # All retries exhausted
        if last_error:
            raise last_error
        # This should not happen, but satisfy type checker
        raise OnetRateLimitError("Rate limit exceeded after all retries")
