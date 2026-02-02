# discovery/tests/unit/test_error_registration.py
"""Unit tests for error handler registration."""
import pytest
from fastapi.testclient import TestClient


def test_error_handlers_registered():
    """Test error handlers are registered with app."""
    from app.main import app

    # Check exception handlers exist
    assert len(app.exception_handlers) > 0


def test_returns_json_on_error():
    """Test errors return JSON response."""
    from app.main import app

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/api/v1/sessions/invalid-uuid")

    # Should get JSON error response
    assert response.headers.get("content-type") == "application/json"
