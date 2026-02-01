"""Test all models are exported from package."""
import pytest


def test_all_onet_models_importable():
    """Test all O*NET models can be imported from package."""
    from app.models import (
        OnetOccupation,
        OnetGWA,
        OnetIWA,
        OnetDWA,
        OnetTask,
        OnetTaskToDWA,
        OnetSkill,
        OnetTechnologySkill,
    )

    assert OnetOccupation is not None
    assert OnetGWA is not None
    assert OnetIWA is not None
    assert OnetDWA is not None
    assert OnetTask is not None
    assert OnetTaskToDWA is not None
    assert OnetSkill is not None
    assert OnetTechnologySkill is not None


def test_base_exports():
    """Test base model utilities are exported."""
    from app.models import Base, async_session_maker, get_async_session

    assert Base is not None
    assert async_session_maker is not None
    assert get_async_session is not None
