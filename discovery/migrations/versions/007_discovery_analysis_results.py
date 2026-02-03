"""Create discovery analysis results table.

Revision ID: 007_analysis_results
Revises: 006_activity_selections
Create Date: 2026-02-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "007_analysis_results"
down_revision: Union[str, None] = "006_activity_selections"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "discovery_analysis_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_mapping_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "dimension",
            postgresql.ENUM(
                "role",
                "task",
                "lob",
                "geography",
                "department",
                name="analysis_dimension",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("dimension_value", sa.String(255), nullable=False),
        sa.Column("ai_exposure_score", sa.Float(), nullable=False),
        sa.Column("impact_score", sa.Float(), nullable=True),
        sa.Column("complexity_score", sa.Float(), nullable=True),
        sa.Column("priority_score", sa.Float(), nullable=True),
        sa.Column("breakdown", postgresql.JSONB(), nullable=True),
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
            ondelete="CASCADE",
        ),
    )
    op.create_index("idx_analysis_session", "discovery_analysis_results", ["session_id"])
    op.create_index("idx_analysis_mapping", "discovery_analysis_results", ["role_mapping_id"])
    op.create_index("idx_analysis_dimension", "discovery_analysis_results", ["dimension"])


def downgrade() -> None:
    op.drop_index("idx_analysis_dimension", table_name="discovery_analysis_results")
    op.drop_index("idx_analysis_mapping", table_name="discovery_analysis_results")
    op.drop_index("idx_analysis_session", table_name="discovery_analysis_results")
    op.drop_table("discovery_analysis_results")
