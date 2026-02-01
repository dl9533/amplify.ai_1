"""Agent memory models for discovery orchestrator subagents.

This module provides SQLAlchemy models for the three-tier memory hierarchy
used by discovery subagents:

Memory Hierarchy:
- **Working Memory**: Short-term, session-scoped context that expires when
  the session ends. Used for maintaining conversation context within a session.
- **Episodic Memory**: Specific interactions/events stored per organization
  with relevance scoring. Records individual episodes that can be recalled.
- **Semantic Memory**: Learned facts/patterns consolidated from episodic memory
  with confidence scoring. Represents generalized knowledge.

The agent_type field identifies which subagent owns the memory:
- "upload": File upload processing agent
- "mapping": Role-to-O*NET mapping agent
- "activity": Activity selection agent
- "analysis": Scoring and analysis agent
- "roadmap": Candidate recommendation agent
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class AgentMemoryWorking(Base, TimestampMixin):
    """Working memory for session-scoped agent context.

    Stores short-term context that persists for the duration of a discovery
    session. This memory is ephemeral and should be cleaned up when the
    session expires or completes.

    Attributes:
        id: Unique identifier for the memory entry.
        agent_type: Identifies which subagent owns this memory (e.g., "upload", "mapping").
        session_id: Reference to the discovery session this context belongs to.
        context: JSON object containing the working memory state.
        expires_at: When this memory entry should be considered stale/expired.
    """

    __tablename__ = "agent_memory_working"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    agent_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    context: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class AgentMemoryEpisodic(Base, TimestampMixin):
    """Episodic memory for storing specific agent interactions.

    Records individual episodes/events that occurred during discovery sessions.
    These memories are organization-scoped and include relevance scoring for
    retrieval prioritization.

    Attributes:
        id: Unique identifier for the episode.
        agent_type: Identifies which subagent created this episode.
        organization_id: Organization this memory belongs to.
        episode_type: Categorizes the type of episode (e.g., "role_mapping", "error").
        content: JSON object containing the episode details.
        relevance_score: Score indicating how relevant this episode is (0.0-1.0).
    """

    __tablename__ = "agent_memory_episodic"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    agent_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    episode_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    content: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    relevance_score: Mapped[float | None] = mapped_column(Float, nullable=True)


class AgentMemorySemantic(Base, TimestampMixin):
    """Semantic memory for storing learned facts and patterns.

    Represents consolidated knowledge derived from episodic memories.
    These are generalized facts/patterns with confidence scoring that
    improves as more evidence accumulates.

    Attributes:
        id: Unique identifier for the fact.
        agent_type: Identifies which subagent learned this fact.
        organization_id: Organization this knowledge belongs to.
        fact_type: Categorizes the type of fact (e.g., "mapping_preference", "pattern").
        content: JSON object containing the learned fact/pattern.
        confidence: Confidence score for this fact (0.0-1.0).
        occurrence_count: How many times this fact has been observed/reinforced.
        last_updated: When this fact was last updated/reinforced.
    """

    __tablename__ = "agent_memory_semantic"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    agent_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    fact_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    content: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    occurrence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
