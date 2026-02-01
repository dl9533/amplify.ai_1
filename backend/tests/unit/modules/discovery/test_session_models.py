# backend/tests/unit/modules/discovery/test_session_models.py
import pytest

from app.modules.discovery.models.session import (
    DiscoverySession,
    DiscoveryUpload,
    DiscoveryRoleMapping,
    DiscoveryActivitySelection,
    DiscoveryAnalysisResult,
    AgentificationCandidate,
)


def test_discovery_session_has_required_columns():
    """DiscoverySession should track wizard state."""
    columns = {c.name for c in DiscoverySession.__table__.columns}
    assert "id" in columns
    assert "user_id" in columns
    assert "organization_id" in columns
    assert "status" in columns
    assert "current_step" in columns
    assert "created_at" in columns
    assert "updated_at" in columns


def test_discovery_upload_has_required_columns():
    """DiscoveryUpload should store file metadata."""
    columns = {c.name for c in DiscoveryUpload.__table__.columns}
    assert "id" in columns
    assert "session_id" in columns
    assert "file_name" in columns
    assert "file_url" in columns
    assert "row_count" in columns
    assert "column_mappings" in columns
    assert "detected_schema" in columns


def test_discovery_role_mapping_has_required_columns():
    """DiscoveryRoleMapping should link roles to O*NET."""
    columns = {c.name for c in DiscoveryRoleMapping.__table__.columns}
    assert "id" in columns
    assert "session_id" in columns
    assert "source_role" in columns
    assert "onet_code" in columns
    assert "confidence_score" in columns
    assert "user_confirmed" in columns
    assert "row_count" in columns


def test_discovery_activity_selection_has_required_columns():
    """DiscoveryActivitySelection should track DWA selections."""
    columns = {c.name for c in DiscoveryActivitySelection.__table__.columns}
    assert "id" in columns
    assert "session_id" in columns
    assert "role_mapping_id" in columns
    assert "dwa_id" in columns
    assert "selected" in columns
    assert "user_modified" in columns


def test_discovery_analysis_result_has_required_columns():
    """DiscoveryAnalysisResult should store scores."""
    columns = {c.name for c in DiscoveryAnalysisResult.__table__.columns}
    assert "id" in columns
    assert "session_id" in columns
    assert "role_mapping_id" in columns
    assert "dimension" in columns
    assert "dimension_value" in columns
    assert "ai_exposure_score" in columns
    assert "impact_score" in columns
    assert "complexity_score" in columns
    assert "priority_score" in columns
    assert "breakdown" in columns


def test_agentification_candidate_has_required_columns():
    """AgentificationCandidate should track roadmap items."""
    columns = {c.name for c in AgentificationCandidate.__table__.columns}
    assert "id" in columns
    assert "session_id" in columns
    assert "role_mapping_id" in columns
    assert "name" in columns
    assert "description" in columns
    assert "priority_tier" in columns
    assert "estimated_impact" in columns
    assert "selected_for_build" in columns
    assert "intake_request_id" in columns
