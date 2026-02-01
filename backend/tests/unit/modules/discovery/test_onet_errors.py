# backend/tests/unit/modules/discovery/test_onet_errors.py
"""Unit tests for O*NET API error handling.

Tests use respx library to mock HTTP responses at the httpx.AsyncClient level,
providing realistic testing of the _get method boundary without mocking internals.
"""

import pytest
import respx
import httpx

from app.modules.discovery.services.onet_client import OnetApiClient
from app.modules.discovery.exceptions import (
    OnetApiError,
    OnetRateLimitError,
    OnetNotFoundError,
)


@pytest.fixture
def onet_client():
    """Create an O*NET client for testing."""
    return OnetApiClient(api_key="test_key")


# =============================================================================
# Issue #1 Fix: Tests using respx instead of mock-heavy approach
# =============================================================================


@respx.mock
@pytest.mark.asyncio
async def test_rate_limit_error_raises_specific_exception(onet_client):
    """Should raise OnetRateLimitError on 429 response."""
    respx.get("https://services.onetcenter.org/ws/mnm/search").mock(
        return_value=httpx.Response(429, json={"error": "Rate limit exceeded"})
    )

    with pytest.raises(OnetRateLimitError) as exc_info:
        await onet_client.search_occupations("test")

    assert exc_info.value.status_code == 429


@respx.mock
@pytest.mark.asyncio
async def test_not_found_error_raises_specific_exception(onet_client):
    """Should raise OnetNotFoundError on 404 response."""
    respx.get("https://services.onetcenter.org/ws/online/occupations/99-9999.99").mock(
        return_value=httpx.Response(404, json={"error": "Not found"})
    )

    with pytest.raises(OnetNotFoundError) as exc_info:
        await onet_client.get_occupation("99-9999.99")

    assert exc_info.value.status_code == 404
    assert "99-9999.99" in exc_info.value.resource


@respx.mock
@pytest.mark.asyncio
async def test_generic_api_error(onet_client):
    """Should raise OnetApiError on other HTTP errors."""
    respx.get("https://services.onetcenter.org/ws/mnm/search").mock(
        return_value=httpx.Response(500, json={"error": "Internal server error"})
    )

    with pytest.raises(OnetApiError) as exc_info:
        await onet_client.search_occupations("test")

    assert exc_info.value.status_code == 500


@respx.mock
@pytest.mark.asyncio
async def test_exponential_backoff_on_rate_limit(onet_client):
    """Should implement exponential backoff on rate limit."""
    call_count = 0

    def side_effect(request):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            return httpx.Response(429, json={"error": "Rate limit exceeded"})
        return httpx.Response(200, json={"occupation": []})

    respx.get("https://services.onetcenter.org/ws/mnm/search").mock(side_effect=side_effect)

    result = await onet_client.search_occupations_with_retry(
        "test", max_retries=3, base_delay=0.01
    )
    assert call_count == 3
    assert result == []


# =============================================================================
# Issue #3 Fix: Tests for Retry-After header parsing
# =============================================================================


@respx.mock
@pytest.mark.asyncio
async def test_retry_after_header_parsed_correctly(onet_client):
    """Should parse Retry-After header from 429 response."""
    respx.get("https://services.onetcenter.org/ws/mnm/search").mock(
        return_value=httpx.Response(
            429,
            headers={"Retry-After": "60"},
            json={"error": "Rate limit exceeded"},
        )
    )

    with pytest.raises(OnetRateLimitError) as exc_info:
        await onet_client.search_occupations("test")

    assert exc_info.value.retry_after == 60


@respx.mock
@pytest.mark.asyncio
async def test_retry_after_header_invalid_value_handled(onet_client):
    """Should handle invalid Retry-After header values gracefully."""
    respx.get("https://services.onetcenter.org/ws/mnm/search").mock(
        return_value=httpx.Response(
            429,
            headers={"Retry-After": "invalid"},
            json={"error": "Rate limit exceeded"},
        )
    )

    with pytest.raises(OnetRateLimitError) as exc_info:
        await onet_client.search_occupations("test")

    # Should not crash, retry_after should be None for invalid values
    assert exc_info.value.retry_after is None


@respx.mock
@pytest.mark.asyncio
async def test_retry_after_header_missing(onet_client):
    """Should handle missing Retry-After header."""
    respx.get("https://services.onetcenter.org/ws/mnm/search").mock(
        return_value=httpx.Response(
            429,
            json={"error": "Rate limit exceeded"},
        )
    )

    with pytest.raises(OnetRateLimitError) as exc_info:
        await onet_client.search_occupations("test")

    assert exc_info.value.retry_after is None


# =============================================================================
# Issue #4 Fix: Tests for non-rate-limit errors in retry method
# =============================================================================


@respx.mock
@pytest.mark.asyncio
async def test_retry_does_not_retry_not_found_errors(onet_client):
    """Should not retry on 404 errors - propagates immediately."""
    call_count = 0

    def side_effect(request):
        nonlocal call_count
        call_count += 1
        return httpx.Response(404, json={"error": "Not found"})

    respx.get("https://services.onetcenter.org/ws/mnm/search").mock(side_effect=side_effect)

    with pytest.raises(OnetNotFoundError):
        await onet_client.search_occupations_with_retry("test", max_retries=3)

    # Should only be called once - no retries for 404
    assert call_count == 1


@respx.mock
@pytest.mark.asyncio
async def test_retry_does_not_retry_server_errors(onet_client):
    """Should not retry on 500 errors - propagates immediately."""
    call_count = 0

    def side_effect(request):
        nonlocal call_count
        call_count += 1
        return httpx.Response(500, json={"error": "Internal server error"})

    respx.get("https://services.onetcenter.org/ws/mnm/search").mock(side_effect=side_effect)

    with pytest.raises(OnetApiError):
        await onet_client.search_occupations_with_retry("test", max_retries=3)

    # Should only be called once - no retries for 500
    assert call_count == 1


# =============================================================================
# Issue #2 Fix: Test for max_retries validation
# =============================================================================


@pytest.mark.asyncio
async def test_max_retries_must_be_at_least_one(onet_client):
    """Should raise ValueError when max_retries is less than 1."""
    with pytest.raises(ValueError) as exc_info:
        await onet_client.search_occupations_with_retry("test", max_retries=0)

    assert "max_retries must be >= 1" in str(exc_info.value)


@pytest.mark.asyncio
async def test_max_retries_negative_raises_error(onet_client):
    """Should raise ValueError when max_retries is negative."""
    with pytest.raises(ValueError) as exc_info:
        await onet_client.search_occupations_with_retry("test", max_retries=-1)

    assert "max_retries must be >= 1" in str(exc_info.value)


# =============================================================================
# Issue #5 Fix: Tests for input validation
# =============================================================================


@pytest.mark.asyncio
async def test_empty_keyword_raises_error(onet_client):
    """Should raise ValueError when keyword is empty."""
    with pytest.raises(ValueError) as exc_info:
        await onet_client.search_occupations("")

    assert "keyword cannot be empty" in str(exc_info.value)


@pytest.mark.asyncio
async def test_whitespace_keyword_raises_error(onet_client):
    """Should raise ValueError when keyword is only whitespace."""
    with pytest.raises(ValueError) as exc_info:
        await onet_client.search_occupations("   ")

    assert "keyword cannot be empty" in str(exc_info.value)


@pytest.mark.asyncio
async def test_negative_base_delay_raises_error(onet_client):
    """Should raise ValueError when base_delay is negative."""
    with pytest.raises(ValueError) as exc_info:
        await onet_client.search_occupations_with_retry("test", base_delay=-1.0)

    assert "base_delay must be non-negative" in str(exc_info.value)


@respx.mock
@pytest.mark.asyncio
async def test_zero_base_delay_is_allowed(onet_client):
    """Should allow base_delay of 0."""
    respx.get("https://services.onetcenter.org/ws/mnm/search").mock(
        return_value=httpx.Response(200, json={"occupation": []})
    )

    # Should not raise - 0 is a valid value for base_delay
    result = await onet_client.search_occupations_with_retry("test", base_delay=0.0)
    assert result == []


@pytest.mark.asyncio
async def test_retry_empty_keyword_raises_error(onet_client):
    """Should raise ValueError when keyword is empty in retry method."""
    with pytest.raises(ValueError) as exc_info:
        await onet_client.search_occupations_with_retry("")

    assert "keyword cannot be empty" in str(exc_info.value)
