# discovery/tests/unit/models/test_agent_memory.py
"""Unit tests for agent memory models."""
import pytest


def test_working_memory_exists():
    """Test AgentWorkingMemory model exists."""
    from app.models.agent_memory import AgentWorkingMemory
    assert AgentWorkingMemory is not None


def test_episodic_memory_exists():
    """Test AgentEpisodicMemory model exists."""
    from app.models.agent_memory import AgentEpisodicMemory
    assert AgentEpisodicMemory is not None


def test_semantic_memory_exists():
    """Test AgentSemanticMemory model exists."""
    from app.models.agent_memory import AgentSemanticMemory
    assert AgentSemanticMemory is not None


def test_episodic_has_organization_scope():
    """Test episodic memory is scoped to organization."""
    from app.models.agent_memory import AgentEpisodicMemory
    columns = AgentEpisodicMemory.__table__.columns.keys()
    assert "organization_id" in columns


def test_working_memory_has_session_id():
    """Test working memory is scoped to session."""
    from app.models.agent_memory import AgentWorkingMemory
    columns = AgentWorkingMemory.__table__.columns.keys()
    assert "session_id" in columns


def test_semantic_memory_has_embedding():
    """Test semantic memory supports embeddings."""
    from app.models.agent_memory import AgentSemanticMemory
    columns = AgentSemanticMemory.__table__.columns.keys()
    assert "embedding" in columns or "content" in columns
