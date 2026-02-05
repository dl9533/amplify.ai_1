"""Create discovery task selections table.

Revision ID: 017_task_selections
Revises: 016_add_onet_task_id
Create Date: 2026-02-05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "017_task_selections"
down_revision: Union[str, None] = "016_add_onet_task_id"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "discovery_task_selections",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_mapping_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("selected", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("user_modified", sa.Boolean(), server_default="false", nullable=False),
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
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["onet_tasks.id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index("idx_task_sel_session", "discovery_task_selections", ["session_id"])
    op.create_index("idx_task_sel_mapping", "discovery_task_selections", ["role_mapping_id"])
    op.create_index("idx_task_sel_task", "discovery_task_selections", ["task_id"])
    # Prevent duplicate task selections per role mapping
    op.create_index(
        "uq_task_sel_mapping_task",
        "discovery_task_selections",
        ["role_mapping_id", "task_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_task_sel_mapping_task", table_name="discovery_task_selections")
    op.drop_index("idx_task_sel_task", table_name="discovery_task_selections")
    op.drop_index("idx_task_sel_mapping", table_name="discovery_task_selections")
    op.drop_index("idx_task_sel_session", table_name="discovery_task_selections")
    op.drop_table("discovery_task_selections")
