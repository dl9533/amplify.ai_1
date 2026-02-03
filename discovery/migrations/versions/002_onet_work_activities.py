"""Create O*NET work activity hierarchy tables.

Revision ID: 002_work_activities
Revises: 001_onet_alt_sync
Create Date: 2026-02-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "002_work_activities"
down_revision: Union[str, None] = "001_onet_alt_sync"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create onet_iwa table (Intermediate Work Activities)
    op.create_table(
        "onet_iwa",
        sa.Column("id", sa.String(20), nullable=False),
        sa.Column("gwa_id", sa.String(20), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["gwa_id"],
            ["onet_gwa.id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index("idx_iwa_gwa", "onet_iwa", ["gwa_id"])

    # Create onet_dwa table (Detailed Work Activities)
    op.create_table(
        "onet_dwa",
        sa.Column("id", sa.String(20), nullable=False),
        sa.Column("iwa_id", sa.String(20), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("ai_exposure_override", sa.Float(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["iwa_id"],
            ["onet_iwa.id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index("idx_dwa_iwa", "onet_dwa", ["iwa_id"])


def downgrade() -> None:
    op.drop_index("idx_dwa_iwa", table_name="onet_dwa")
    op.drop_table("onet_dwa")

    op.drop_index("idx_iwa_gwa", table_name="onet_iwa")
    op.drop_table("onet_iwa")
