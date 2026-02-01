"""Unit tests for O*NET work activity models."""
import pytest


def test_gwa_model_exists():
    """Test OnetGWA model is importable."""
    from app.models.onet_work_activities import OnetGWA
    assert OnetGWA is not None


def test_iwa_model_exists():
    """Test OnetIWA model is importable."""
    from app.models.onet_work_activities import OnetIWA
    assert OnetIWA is not None


def test_dwa_model_exists():
    """Test OnetDWA model is importable."""
    from app.models.onet_work_activities import OnetDWA
    assert OnetDWA is not None


def test_gwa_has_ai_exposure_score():
    """Test GWA has AI exposure score column."""
    from app.models.onet_work_activities import OnetGWA
    columns = OnetGWA.__table__.columns.keys()
    assert "ai_exposure_score" in columns


def test_iwa_has_gwa_foreign_key():
    """Test IWA references GWA."""
    from app.models.onet_work_activities import OnetIWA
    columns = OnetIWA.__table__.columns.keys()
    assert "gwa_id" in columns


def test_dwa_has_iwa_foreign_key():
    """Test DWA references IWA."""
    from app.models.onet_work_activities import OnetDWA
    columns = OnetDWA.__table__.columns.keys()
    assert "iwa_id" in columns


def test_dwa_has_ai_exposure_override():
    """Test DWA has optional AI exposure override."""
    from app.models.onet_work_activities import OnetDWA
    columns = OnetDWA.__table__.columns.keys()
    assert "ai_exposure_override" in columns
