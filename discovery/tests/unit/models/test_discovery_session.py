"""Unit tests for DiscoverySession model."""
import pytest


def test_discovery_session_model_exists():
    """Test DiscoverySession model is importable."""
    from app.models.discovery_session import DiscoverySession, SessionStatus
    assert DiscoverySession is not None
    assert SessionStatus is not None


def test_session_has_required_columns():
    """Test model has required columns."""
    from app.models.discovery_session import DiscoverySession

    columns = DiscoverySession.__table__.columns.keys()
    assert "id" in columns
    assert "user_id" in columns
    assert "organization_id" in columns
    assert "status" in columns
    assert "current_step" in columns


def test_session_status_enum_values():
    """Test SessionStatus has expected values."""
    from app.models.discovery_session import SessionStatus

    assert SessionStatus.DRAFT.value == "draft"
    assert SessionStatus.IN_PROGRESS.value == "in_progress"
    assert SessionStatus.COMPLETED.value == "completed"
    assert SessionStatus.ARCHIVED.value == "archived"
