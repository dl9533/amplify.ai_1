# discovery/tests/unit/test_all_dependencies.py
"""Unit tests for all dependencies."""
import pytest


def test_all_service_dependencies_exist():
    """Test all service dependencies are defined."""
    from app.dependencies import (
        get_session_service_dep,
        get_upload_service_dep,
        get_role_mapping_service_dep,
        get_activity_service_dep,
        get_analysis_service_dep,
        get_roadmap_service_dep,
        get_chat_service_dep,
    )

    assert get_session_service_dep is not None
    assert get_upload_service_dep is not None
    assert get_role_mapping_service_dep is not None
    assert get_activity_service_dep is not None
    assert get_analysis_service_dep is not None
    assert get_roadmap_service_dep is not None
    assert get_chat_service_dep is not None


def test_all_repository_dependencies_exist():
    """Test all repository dependencies are defined."""
    from app.dependencies import (
        get_session_repository,
        get_upload_repository,
        get_role_mapping_repository,
        get_activity_selection_repository,
        get_analysis_repository,
        get_candidate_repository,
        get_onet_repository,
    )

    assert get_session_repository is not None
    assert get_upload_repository is not None
    assert get_role_mapping_repository is not None
    assert get_activity_selection_repository is not None
    assert get_analysis_repository is not None
    assert get_candidate_repository is not None
    assert get_onet_repository is not None
