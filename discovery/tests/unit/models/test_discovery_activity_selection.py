"""Unit tests for DiscoveryActivitySelection model."""
import pytest


def test_activity_selection_model_exists():
    """Test DiscoveryActivitySelection model is importable."""
    from app.models.discovery_activity_selection import DiscoveryActivitySelection
    assert DiscoveryActivitySelection is not None


def test_activity_selection_has_required_columns():
    """Test model has required columns."""
    from app.models.discovery_activity_selection import DiscoveryActivitySelection

    columns = DiscoveryActivitySelection.__table__.columns.keys()
    assert "id" in columns
    assert "session_id" in columns
    assert "role_mapping_id" in columns
    assert "dwa_id" in columns
    assert "selected" in columns
    assert "user_modified" in columns
