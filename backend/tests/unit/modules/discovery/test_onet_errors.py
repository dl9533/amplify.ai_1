# backend/tests/unit/modules/discovery/test_onet_errors.py
"""Unit tests for O*NET API error handling."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.modules.discovery.services.onet_client import OnetApiClient
from app.modules.discovery.exceptions import (
    OnetApiError,
    OnetRateLimitError,
    OnetNotFoundError,
)


@pytest.fixture
def onet_client():
    return OnetApiClient(api_key="test_key")


def create_mock_response(status_code: int):
    """Create a mock httpx response with the given status code."""
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.headers = {}
    return mock_response


@pytest.mark.asyncio
async def test_rate_limit_error_raises_specific_exception(onet_client):
    """Should raise OnetRateLimitError on 429 response."""
    mock_response = create_mock_response(429)
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Rate limited", request=MagicMock(), response=mock_response
    )

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response

    with patch("httpx.AsyncClient") as mock_async_client:
        mock_async_client.return_value.__aenter__.return_value = mock_client

        with pytest.raises(OnetRateLimitError):
            await onet_client.search_occupations("test")


@pytest.mark.asyncio
async def test_not_found_error_raises_specific_exception(onet_client):
    """Should raise OnetNotFoundError on 404 response."""
    mock_response = create_mock_response(404)
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Not found", request=MagicMock(), response=mock_response
    )

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response

    with patch("httpx.AsyncClient") as mock_async_client:
        mock_async_client.return_value.__aenter__.return_value = mock_client

        with pytest.raises(OnetNotFoundError):
            await onet_client.get_occupation("99-9999.99")


@pytest.mark.asyncio
async def test_generic_api_error(onet_client):
    """Should raise OnetApiError on other HTTP errors."""
    mock_response = create_mock_response(500)
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Server error", request=MagicMock(), response=mock_response
    )

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response

    with patch("httpx.AsyncClient") as mock_async_client:
        mock_async_client.return_value.__aenter__.return_value = mock_client

        with pytest.raises(OnetApiError):
            await onet_client.search_occupations("test")


@pytest.mark.asyncio
async def test_exponential_backoff_on_rate_limit(onet_client):
    """Should implement exponential backoff on rate limit."""
    call_count = 0

    async def mock_get(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise OnetRateLimitError("Rate limited")
        return {"occupation": []}

    with patch.object(onet_client, "_get", side_effect=mock_get):
        result = await onet_client.search_occupations_with_retry("test", max_retries=3)
        assert call_count == 3
