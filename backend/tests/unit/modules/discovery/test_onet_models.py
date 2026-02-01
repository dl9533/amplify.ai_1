# backend/tests/unit/modules/discovery/test_onet_models.py
import pytest

from app.modules.discovery.models.onet import (
    OnetOccupation,
    OnetGwa,
    OnetIwa,
    OnetDwa,
    OnetTask,
    OnetSkill,
    OnetTechnologySkill,
)


def test_onet_occupation_has_required_columns():
    """OnetOccupation model should have O*NET occupation columns."""
    columns = {c.name for c in OnetOccupation.__table__.columns}
    assert "code" in columns  # PK, e.g., "15-1252.00"
    assert "title" in columns
    assert "description" in columns
    assert "updated_at" in columns


def test_onet_gwa_has_required_columns():
    """OnetGwa model should have generalized work activity columns."""
    columns = {c.name for c in OnetGwa.__table__.columns}
    assert "id" in columns  # e.g., "4.A.1.a.1"
    assert "name" in columns
    assert "description" in columns
    assert "ai_exposure_score" in columns  # 0.0-1.0


def test_onet_iwa_has_required_columns():
    """OnetIwa model should have intermediate work activity columns."""
    columns = {c.name for c in OnetIwa.__table__.columns}
    assert "id" in columns
    assert "gwa_id" in columns  # FK to OnetGwa
    assert "name" in columns
    assert "description" in columns


def test_onet_dwa_has_required_columns():
    """OnetDwa model should have detailed work activity columns."""
    columns = {c.name for c in OnetDwa.__table__.columns}
    assert "id" in columns
    assert "iwa_id" in columns  # FK to OnetIwa
    assert "name" in columns
    assert "description" in columns
    assert "ai_exposure_override" in columns  # NULL = inherit from GWA


def test_onet_task_has_required_columns():
    """OnetTask model should have task columns."""
    columns = {c.name for c in OnetTask.__table__.columns}
    assert "id" in columns
    assert "occupation_code" in columns  # FK to OnetOccupation
    assert "description" in columns
    assert "importance" in columns


def test_onet_skill_has_required_columns():
    """OnetSkill model should have skill columns."""
    columns = {c.name for c in OnetSkill.__table__.columns}
    assert "id" in columns
    assert "name" in columns
    assert "description" in columns


def test_onet_technology_skill_has_required_columns():
    """OnetTechnologySkill model should have tech skill columns."""
    columns = {c.name for c in OnetTechnologySkill.__table__.columns}
    assert "id" in columns
    assert "occupation_code" in columns
    assert "technology_name" in columns
    assert "hot_technology" in columns
