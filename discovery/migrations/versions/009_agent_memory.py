"""Create agent memory tables.

Revision ID: 009_agent_memory
Revises: 008_agentification
Create Date: 2026-02-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "009_agent_memory"
down_revision: Union[str, None] = "008_agentification"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create agent_memory_working table (session-scoped context)
    op.create_table(
        "agent_memory_working",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_type", sa.String(50), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("context", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["discovery_sessions.id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index("idx_working_mem_session", "agent_memory_working", ["session_id"])
    op.create_index("idx_working_mem_agent", "agent_memory_working", ["agent_type"])
    op.create_index("idx_working_mem_expires", "agent_memory_working", ["expires_at"])

    # Create agent_memory_episodic table (specific interactions for learning)
    op.create_table(
        "agent_memory_episodic",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_type", sa.String(50), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("episode_type", sa.String(50), nullable=False),
        sa.Column("content", postgresql.JSONB(), nullable=False),
        sa.Column("relevance_score", sa.Float(), server_default="1.0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_episodic_mem_org", "agent_memory_episodic", ["organization_id"])
    op.create_index("idx_episodic_mem_agent", "agent_memory_episodic", ["agent_type"])
    op.create_index("idx_episodic_mem_type", "agent_memory_episodic", ["episode_type"])

    # Create agent_memory_semantic table (learned patterns and facts)
    op.create_table(
        "agent_memory_semantic",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_type", sa.String(50), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("fact_key", sa.String(255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", postgresql.JSONB(), nullable=True),
        sa.Column("confidence", sa.Float(), server_default="1.0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_semantic_mem_org", "agent_memory_semantic", ["organization_id"])
    op.create_index("idx_semantic_mem_agent", "agent_memory_semantic", ["agent_type"])
    op.create_index("idx_semantic_mem_category", "agent_memory_semantic", ["category"])
    op.create_index("idx_semantic_mem_fact", "agent_memory_semantic", ["fact_key"])


def downgrade() -> None:
    op.drop_index("idx_semantic_mem_fact", table_name="agent_memory_semantic")
    op.drop_index("idx_semantic_mem_category", table_name="agent_memory_semantic")
    op.drop_index("idx_semantic_mem_agent", table_name="agent_memory_semantic")
    op.drop_index("idx_semantic_mem_org", table_name="agent_memory_semantic")
    op.drop_table("agent_memory_semantic")

    op.drop_index("idx_episodic_mem_type", table_name="agent_memory_episodic")
    op.drop_index("idx_episodic_mem_agent", table_name="agent_memory_episodic")
    op.drop_index("idx_episodic_mem_org", table_name="agent_memory_episodic")
    op.drop_table("agent_memory_episodic")

    op.drop_index("idx_working_mem_expires", table_name="agent_memory_working")
    op.drop_index("idx_working_mem_agent", table_name="agent_memory_working")
    op.drop_index("idx_working_mem_session", table_name="agent_memory_working")
    op.drop_table("agent_memory_working")
