# discovery/tests/unit/middleware/test_error_handler.py
"""Unit tests for error handler middleware."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_error_handler_exists():
    """Test error handler is importable."""
    from app.middleware.error_handler import add_exception_handlers
    assert add_exception_handlers is not None


def test_handles_session_not_found():
    """Test 404 response for session not found."""
    from app.middleware.error_handler import add_exception_handlers
    from app.exceptions import SessionNotFoundException

    app = FastAPI()
    add_exception_handlers(app)

    @app.get("/test")
    async def test_route():
        raise SessionNotFoundException("test-id")

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/test")

    assert response.status_code == 404
    assert "Session not found" in response.json()["detail"]


def test_handles_validation_error():
    """Test 422 response for validation error."""
    from app.middleware.error_handler import add_exception_handlers
    from app.exceptions import ValidationException

    app = FastAPI()
    add_exception_handlers(app)

    @app.get("/test")
    async def test_route():
        raise ValidationException("Invalid input", {"field": "name"})

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/test")

    assert response.status_code == 422
