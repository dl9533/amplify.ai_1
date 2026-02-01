"""Unit tests for O*NET skills models."""
import pytest


def test_onet_skill_model_exists():
    """Test OnetSkill model is importable."""
    from app.models.onet_skills import OnetSkill
    assert OnetSkill is not None


def test_onet_technology_skill_exists():
    """Test OnetTechnologySkill model is importable."""
    from app.models.onet_skills import OnetTechnologySkill
    assert OnetTechnologySkill is not None


def test_technology_skill_has_hot_flag():
    """Test technology skill has hot_technology flag."""
    from app.models.onet_skills import OnetTechnologySkill
    columns = OnetTechnologySkill.__table__.columns.keys()
    assert "hot_technology" in columns
