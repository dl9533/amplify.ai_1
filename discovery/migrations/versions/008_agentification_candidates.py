"""Create agentification candidates table.

Revision ID: 008_agentification
Revises: 007_analysis_results
Create Date: 2026-02-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "008_agentification"
down_revision: Union[str, None] = "007_analysis_results"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agentification_candidates",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_mapping_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "priority_tier",
            postgresql.ENUM(
                "now",
                "next_quarter",
                "future",
                name="priority_tier",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("estimated_impact", sa.Float(), nullable=True),
        sa.Column("selected_for_build", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("intake_request_id", postgresql.UUID(as_uuid=True), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["role_mapping_id"],
            ["discovery_role_mappings.id"],
            ondelete="SET NULL",
        ),
    )
    op.create_index("idx_candidate_session", "agentification_candidates", ["session_id"])
    op.create_index("idx_candidate_mapping", "agentification_candidates", ["role_mapping_id"])
    op.create_index("idx_candidate_priority", "agentification_candidates", ["priority_tier"])


def downgrade() -> None:
    op.drop_index("idx_candidate_priority", table_name="agentification_candidates")
    op.drop_index("idx_candidate_mapping", table_name="agentification_candidates")
    op.drop_index("idx_candidate_session", table_name="agentification_candidates")
    op.drop_table("agentification_candidates")
