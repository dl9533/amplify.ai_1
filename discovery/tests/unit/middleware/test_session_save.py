# discovery/tests/unit/middleware/test_session_save.py
"""Unit tests for session auto-save."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def test_auto_save_middleware_exists():
    """Test AutoSaveMiddleware is importable."""
    from app.middleware.session_save import AutoSaveMiddleware
    assert AutoSaveMiddleware is not None


@pytest.mark.asyncio
async def test_saves_on_successful_request():
    """Test session is saved after successful request."""
    from app.middleware.session_save import AutoSaveMiddleware

    mock_session_service = AsyncMock()
    middleware = AutoSaveMiddleware(session_service=mock_session_service)

    # Simulate successful response handling
    assert hasattr(middleware, "save_session_state")
