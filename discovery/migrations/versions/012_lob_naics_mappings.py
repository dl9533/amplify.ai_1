"""LOB to NAICS code mappings table.

Revision ID: 012_lob_naics_mappings
Revises: 011_naics_codes
Create Date: 2026-02-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "012_lob_naics_mappings"
down_revision: Union[str, None] = "011_naics_codes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create lob_naics_mappings table."""
    op.create_table(
        "lob_naics_mappings",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("lob_pattern", sa.String(255), nullable=False, unique=True),
        sa.Column("naics_codes", postgresql.ARRAY(sa.String(6)), nullable=False),
        sa.Column("confidence", sa.Float, nullable=False, server_default="1.0"),
        sa.Column("source", sa.String(50), nullable=False, server_default="curated"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_lob_pattern", "lob_naics_mappings", ["lob_pattern"])


def downgrade() -> None:
    """Drop lob_naics_mappings table."""
    op.drop_index("idx_lob_pattern", table_name="lob_naics_mappings")
    op.drop_table("lob_naics_mappings")
