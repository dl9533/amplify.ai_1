"""Unit tests for OnetOccupation model."""
import pytest


def test_onet_occupation_model_exists():
    """Test that OnetOccupation model is importable."""
    from app.models.onet_occupation import OnetOccupation
    assert OnetOccupation is not None


def test_onet_occupation_has_required_columns():
    """Test that model has all required columns."""
    from app.models.onet_occupation import OnetOccupation

    columns = OnetOccupation.__table__.columns.keys()
    assert "code" in columns
    assert "title" in columns
    assert "description" in columns
    assert "updated_at" in columns


def test_onet_occupation_code_is_primary_key():
    """Test that code is the primary key."""
    from app.models.onet_occupation import OnetOccupation

    pk_columns = [c.name for c in OnetOccupation.__table__.primary_key.columns]
    assert pk_columns == ["code"]
