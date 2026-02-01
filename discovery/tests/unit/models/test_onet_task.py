"""Unit tests for OnetTask model."""
import pytest


def test_onet_task_model_exists():
    """Test OnetTask model is importable."""
    from app.models.onet_task import OnetTask
    assert OnetTask is not None


def test_onet_task_has_required_columns():
    """Test model has required columns."""
    from app.models.onet_task import OnetTask

    columns = OnetTask.__table__.columns.keys()
    assert "id" in columns
    assert "occupation_code" in columns
    assert "description" in columns
    assert "importance" in columns


def test_onet_task_to_dwa_exists():
    """Test junction table model exists."""
    from app.models.onet_task import OnetTaskToDWA
    assert OnetTaskToDWA is not None
