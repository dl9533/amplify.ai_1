"""Create O*NET alternate titles and sync log tables.

Revision ID: 001_onet_alt_sync
Revises:
Create Date: 2026-02-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_onet_alt_sync"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create onet_alternate_titles table
    op.create_table(
        "onet_alternate_titles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("onet_code", sa.String(10), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["onet_code"],
            ["onet_occupations.code"],
            ondelete="CASCADE",
        ),
    )
    op.create_index("idx_alt_title_onet_code", "onet_alternate_titles", ["onet_code"])
    op.create_index("idx_alt_title_title", "onet_alternate_titles", ["title"])

    # Create onet_sync_log table
    op.create_table(
        "onet_sync_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.String(20), nullable=False),
        sa.Column(
            "synced_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("occupation_count", sa.Integer(), nullable=False),
        sa.Column("alternate_title_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("task_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create full-text search index on alternate titles
    op.execute("""
        CREATE INDEX idx_onet_alt_title_search
        ON onet_alternate_titles
        USING gin(to_tsvector('english', title))
    """)


def downgrade() -> None:
    op.drop_index("idx_onet_alt_title_search", table_name="onet_alternate_titles")
    op.drop_table("onet_sync_log")
    op.drop_index("idx_alt_title_title", table_name="onet_alternate_titles")
    op.drop_index("idx_alt_title_onet_code", table_name="onet_alternate_titles")
    op.drop_table("onet_alternate_titles")
