"""NAICS reference codes table.

Revision ID: 011_naics_codes
Revises: 010_chat_messages
Create Date: 2026-02-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "011_naics_codes"
down_revision: Union[str, None] = "010_chat_messages"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create naics_codes reference table."""
    op.create_table(
        "naics_codes",
        sa.Column("code", sa.String(6), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("level", sa.Integer, nullable=False),
        sa.Column("parent_code", sa.String(6), sa.ForeignKey("naics_codes.code"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    """Drop naics_codes table."""
    op.drop_table("naics_codes")
