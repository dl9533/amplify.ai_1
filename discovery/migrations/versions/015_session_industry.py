"""Add industry_naics_sector column to discovery_sessions.

Revision ID: 015_session_industry
Revises: 014_add_lob_columns
Create Date: 2026-02-05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "015_session_industry"
down_revision: Union[str, None] = "014_add_lob_columns"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add industry_naics_sector column to discovery_sessions."""
    op.add_column(
        "discovery_sessions",
        sa.Column("industry_naics_sector", sa.String(2), nullable=True),
    )
    # Add index for potential filtering by industry
    op.create_index(
        "idx_sessions_industry",
        "discovery_sessions",
        ["industry_naics_sector"],
    )


def downgrade() -> None:
    """Remove industry_naics_sector column."""
    op.drop_index("idx_sessions_industry", table_name="discovery_sessions")
    op.drop_column("discovery_sessions", "industry_naics_sector")
