"""Add LOB columns to upload and role mapping tables.

Revision ID: 014_add_lob_columns
Revises: 013_onet_occupation_industries
Create Date: 2026-02-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "014_add_lob_columns"
down_revision: Union[str, None] = "013_onet_occupation_industries"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add LOB-related columns to existing tables."""
    # Add lob_column to discovery_uploads
    op.add_column(
        "discovery_uploads",
        sa.Column("lob_column", sa.String(255), nullable=True),
    )

    # Add LOB columns to discovery_role_mappings
    op.add_column(
        "discovery_role_mappings",
        sa.Column("lob_value", sa.String(255), nullable=True),
    )
    op.add_column(
        "discovery_role_mappings",
        sa.Column("naics_codes", postgresql.ARRAY(sa.String(6)), nullable=True),
    )
    op.add_column(
        "discovery_role_mappings",
        sa.Column("industry_match_score", sa.Float, nullable=True),
    )

    # Add index for LOB grouping queries
    op.create_index(
        "idx_role_mappings_lob",
        "discovery_role_mappings",
        ["session_id", "lob_value"],
    )


def downgrade() -> None:
    """Remove LOB columns."""
    op.drop_index("idx_role_mappings_lob", table_name="discovery_role_mappings")
    op.drop_column("discovery_role_mappings", "industry_match_score")
    op.drop_column("discovery_role_mappings", "naics_codes")
    op.drop_column("discovery_role_mappings", "lob_value")
    op.drop_column("discovery_uploads", "lob_column")
