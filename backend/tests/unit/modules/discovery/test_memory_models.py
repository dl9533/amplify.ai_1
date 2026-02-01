"""Unit tests for agent memory models (working, episodic, semantic)."""

import pytest

from app.modules.discovery.models.memory import (
    AgentMemoryWorking,
    AgentMemoryEpisodic,
    AgentMemorySemantic,
)


def test_agent_memory_working_has_required_columns():
    """AgentMemoryWorking should store session-scoped context."""
    columns = {c.name for c in AgentMemoryWorking.__table__.columns}
    assert "id" in columns
    assert "agent_type" in columns
    assert "session_id" in columns
    assert "context" in columns
    assert "expires_at" in columns


def test_agent_memory_episodic_has_required_columns():
    """AgentMemoryEpisodic should store specific interactions."""
    columns = {c.name for c in AgentMemoryEpisodic.__table__.columns}
    assert "id" in columns
    assert "agent_type" in columns
    assert "organization_id" in columns
    assert "episode_type" in columns
    assert "content" in columns
    assert "created_at" in columns
    assert "relevance_score" in columns


def test_agent_memory_semantic_has_required_columns():
    """AgentMemorySemantic should store learned patterns."""
    columns = {c.name for c in AgentMemorySemantic.__table__.columns}
    assert "id" in columns
    assert "agent_type" in columns
    assert "organization_id" in columns
    assert "fact_type" in columns
    assert "content" in columns
    assert "confidence" in columns
    assert "occurrence_count" in columns
    assert "last_updated" in columns
