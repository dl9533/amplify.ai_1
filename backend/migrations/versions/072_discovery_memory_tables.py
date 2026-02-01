"""Discovery agent memory tables migration.

Creates tables for the three-tier memory hierarchy used by discovery subagents:
- agent_memory_working: Short-term, session-scoped context
- agent_memory_episodic: Specific interactions/events per organization
- agent_memory_semantic: Learned facts/patterns with confidence scoring

Revision ID: 072_discovery_memory_tables
Revises: 071_discovery_session_tables
Create Date: 2026-01-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "072_discovery_memory_tables"
down_revision: str | None = "071_discovery_session_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create agent memory tables for discovery subagents."""
    # Create agent_memory_working table
    # Short-term, session-scoped context that expires when the session ends
    op.create_table(
        "agent_memory_working",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("agent_type", sa.String(50), nullable=False, index=True),
        sa.Column(
            "session_id", postgresql.UUID(as_uuid=True), nullable=False, index=True
        ),
        sa.Column("context", postgresql.JSON(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )

    # Create agent_memory_episodic table
    # Specific interactions/events stored per organization with relevance scoring
    op.create_table(
        "agent_memory_episodic",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("agent_type", sa.String(50), nullable=False, index=True),
        sa.Column(
            "organization_id", postgresql.UUID(as_uuid=True), nullable=False, index=True
        ),
        sa.Column("episode_type", sa.String(100), nullable=False, index=True),
        sa.Column("content", postgresql.JSON(), nullable=True),
        sa.Column("relevance_score", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )

    # Create agent_memory_semantic table
    # Learned facts/patterns consolidated from episodic memory with confidence scoring
    op.create_table(
        "agent_memory_semantic",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("agent_type", sa.String(50), nullable=False, index=True),
        sa.Column(
            "organization_id", postgresql.UUID(as_uuid=True), nullable=False, index=True
        ),
        sa.Column("fact_type", sa.String(100), nullable=False, index=True),
        sa.Column("content", postgresql.JSON(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("occurrence_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("last_updated", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Drop all agent memory tables in reverse order of creation."""
    op.drop_table("agent_memory_semantic")
    op.drop_table("agent_memory_episodic")
    op.drop_table("agent_memory_working")
