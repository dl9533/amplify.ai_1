# discovery/tests/unit/test_exceptions.py
"""Unit tests for custom exceptions."""
import pytest


def test_discovery_exception_exists():
    """Test DiscoveryException base class exists."""
    from app.exceptions import DiscoveryException
    assert DiscoveryException is not None


def test_session_not_found_exception():
    """Test SessionNotFoundException."""
    from app.exceptions import SessionNotFoundException

    exc = SessionNotFoundException("abc-123")
    assert "abc-123" in str(exc)


def test_validation_exception():
    """Test ValidationException with details."""
    from app.exceptions import ValidationException

    exc = ValidationException("Invalid file", details={"field": "file"})
    assert exc.details == {"field": "file"}


def test_onet_exception_retry_info():
    """Test OnetApiException with retry info."""
    from app.exceptions import OnetRateLimitError

    exc = OnetRateLimitError("Rate limited", retry_after=60)
    assert exc.retry_after == 60
