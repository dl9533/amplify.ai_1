"""Create discovery role mappings table.

Revision ID: 005_role_mappings
Revises: 004_uploads
Create Date: 2026-02-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "005_role_mappings"
down_revision: Union[str, None] = "004_uploads"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "discovery_role_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_role", sa.String(255), nullable=False),
        sa.Column("onet_code", sa.String(10), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("user_confirmed", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=True),
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
            ["onet_code"],
            ["onet_occupations.code"],
            ondelete="SET NULL",
        ),
    )
    op.create_index("idx_mapping_session", "discovery_role_mappings", ["session_id"])
    op.create_index("idx_mapping_onet", "discovery_role_mappings", ["onet_code"])


def downgrade() -> None:
    op.drop_index("idx_mapping_onet", table_name="discovery_role_mappings")
    op.drop_index("idx_mapping_session", table_name="discovery_role_mappings")
    op.drop_table("discovery_role_mappings")
