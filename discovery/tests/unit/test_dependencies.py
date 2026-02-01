"""Unit tests for dependency injection."""
import pytest


def test_get_db_dependency_exists():
    """Test get_db dependency is importable."""
    from app.dependencies import get_db
    assert get_db is not None


def test_get_session_service_dependency_exists():
    """Test get_session_service_dep is importable."""
    from app.dependencies import get_session_service_dep
    assert get_session_service_dep is not None


def test_get_onet_repository_dependency_exists():
    """Test get_onet_repository is importable."""
    from app.dependencies import get_onet_repository
    assert get_onet_repository is not None


def test_get_session_repository_dependency_exists():
    """Test get_session_repository is importable."""
    from app.dependencies import get_session_repository
    assert get_session_repository is not None


def test_get_upload_repository_dependency_exists():
    """Test get_upload_repository is importable."""
    from app.dependencies import get_upload_repository
    assert get_upload_repository is not None


def test_get_role_mapping_repository_dependency_exists():
    """Test get_role_mapping_repository is importable."""
    from app.dependencies import get_role_mapping_repository
    assert get_role_mapping_repository is not None


def test_get_analysis_repository_dependency_exists():
    """Test get_analysis_repository is importable."""
    from app.dependencies import get_analysis_repository
    assert get_analysis_repository is not None
