"""Unit tests for DiscoveryUpload model."""
import pytest


def test_discovery_upload_model_exists():
    """Test DiscoveryUpload model is importable."""
    from app.models.discovery_upload import DiscoveryUpload
    assert DiscoveryUpload is not None


def test_upload_has_required_columns():
    """Test model has required columns."""
    from app.models.discovery_upload import DiscoveryUpload

    columns = DiscoveryUpload.__table__.columns.keys()
    assert "id" in columns
    assert "session_id" in columns
    assert "file_name" in columns
    assert "file_url" in columns
    assert "row_count" in columns
    assert "column_mappings" in columns
    assert "detected_schema" in columns


def test_upload_has_session_foreign_key():
    """Test upload references session."""
    from app.models.discovery_upload import DiscoveryUpload

    fk_cols = [fk.column.name for fk in DiscoveryUpload.__table__.foreign_keys]
    assert "id" in fk_cols  # session_id -> discovery_sessions.id
