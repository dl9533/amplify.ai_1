"""Test all repositories are exported from package."""
import pytest


def test_all_repositories_importable():
    """Test all repositories can be imported from package."""
    from app.repositories import (
        OnetRepository,
        SessionRepository,
        UploadRepository,
        RoleMappingRepository,
        AnalysisRepository,
    )

    assert OnetRepository is not None
    assert SessionRepository is not None
    assert UploadRepository is not None
    assert RoleMappingRepository is not None
    assert AnalysisRepository is not None


def test_repositories_all_list():
    """Test __all__ contains all repositories."""
    from app import repositories

    expected = [
        "OnetRepository",
        "SessionRepository",
        "UploadRepository",
        "RoleMappingRepository",
        "AnalysisRepository",
    ]

    for name in expected:
        assert name in repositories.__all__
