"""Create discovery uploads table.

Revision ID: 004_uploads
Revises: 003_tasks_skills
Create Date: 2026-02-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "004_uploads"
down_revision: Union[str, None] = "003_tasks_skills"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "discovery_uploads",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("file_url", sa.String(512), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=True),
        sa.Column("column_mappings", postgresql.JSONB(), nullable=True),
        sa.Column("detected_schema", postgresql.JSONB(), nullable=True),
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
    op.create_index("idx_upload_session", "discovery_uploads", ["session_id"])


def downgrade() -> None:
    op.drop_index("idx_upload_session", table_name="discovery_uploads")
    op.drop_table("discovery_uploads")
