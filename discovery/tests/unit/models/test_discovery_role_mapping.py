"""Unit tests for DiscoveryRoleMapping model."""
import pytest


def test_role_mapping_model_exists():
    """Test DiscoveryRoleMapping model is importable."""
    from app.models.discovery_role_mapping import DiscoveryRoleMapping
    assert DiscoveryRoleMapping is not None


def test_role_mapping_has_required_columns():
    """Test model has required columns."""
    from app.models.discovery_role_mapping import DiscoveryRoleMapping

    columns = DiscoveryRoleMapping.__table__.columns.keys()
    assert "id" in columns
    assert "session_id" in columns
    assert "source_role" in columns
    assert "onet_code" in columns
    assert "confidence_score" in columns
    assert "user_confirmed" in columns
    assert "row_count" in columns
