"""Unit tests for AgentificationCandidate model."""
import pytest


def test_agentification_candidate_model_exists():
    """Test AgentificationCandidate model is importable."""
    from app.models.agentification_candidate import AgentificationCandidate, PriorityTier
    assert AgentificationCandidate is not None
    assert PriorityTier is not None


def test_candidate_has_required_columns():
    """Test model has required columns."""
    from app.models.agentification_candidate import AgentificationCandidate

    columns = AgentificationCandidate.__table__.columns.keys()
    assert "id" in columns
    assert "session_id" in columns
    assert "role_mapping_id" in columns
    assert "name" in columns
    assert "description" in columns
    assert "priority_tier" in columns
    assert "estimated_impact" in columns
    assert "selected_for_build" in columns
    assert "intake_request_id" in columns


def test_priority_tier_enum_values():
    """Test PriorityTier has expected values."""
    from app.models.agentification_candidate import PriorityTier

    assert PriorityTier.NOW.value == "now"
    assert PriorityTier.NEXT_QUARTER.value == "next_quarter"
    assert PriorityTier.FUTURE.value == "future"
