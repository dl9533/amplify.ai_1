"""Create discovery activity selections table.

Revision ID: 006_activity_selections
Revises: 005_role_mappings
Create Date: 2026-02-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "006_activity_selections"
down_revision: Union[str, None] = "005_role_mappings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "discovery_activity_selections",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_mapping_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("dwa_id", sa.String(20), nullable=False),
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
            ["dwa_id"],
            ["onet_dwa.id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index("idx_activity_session", "discovery_activity_selections", ["session_id"])
    op.create_index("idx_activity_mapping", "discovery_activity_selections", ["role_mapping_id"])
    op.create_index("idx_activity_dwa", "discovery_activity_selections", ["dwa_id"])


def downgrade() -> None:
    op.drop_index("idx_activity_dwa", table_name="discovery_activity_selections")
    op.drop_index("idx_activity_mapping", table_name="discovery_activity_selections")
    op.drop_index("idx_activity_session", table_name="discovery_activity_selections")
    op.drop_table("discovery_activity_selections")
