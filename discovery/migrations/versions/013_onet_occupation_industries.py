"""O*NET occupation-industry mappings table.

Revision ID: 013_onet_occupation_industries
Revises: 012_lob_naics_mappings
Create Date: 2026-02-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "013_onet_occupation_industries"
down_revision: Union[str, None] = "012_lob_naics_mappings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create onet_occupation_industries table."""
    op.create_table(
        "onet_occupation_industries",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "occupation_code",
            sa.String(10),
            sa.ForeignKey("onet_occupations.code", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("naics_code", sa.String(6), nullable=False),
        sa.Column("naics_title", sa.String(255), nullable=False),
        sa.Column("employment_percent", sa.Float, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("occupation_code", "naics_code", name="uq_occ_naics"),
    )
    op.create_index("idx_onet_occ_ind_occupation", "onet_occupation_industries", ["occupation_code"])
    op.create_index("idx_onet_occ_ind_naics", "onet_occupation_industries", ["naics_code"])


def downgrade() -> None:
    """Drop onet_occupation_industries table."""
    op.drop_index("idx_onet_occ_ind_naics", table_name="onet_occupation_industries")
    op.drop_index("idx_onet_occ_ind_occupation", table_name="onet_occupation_industries")
    op.drop_table("onet_occupation_industries")
