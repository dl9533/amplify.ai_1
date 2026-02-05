"""Add onet_task_id column to onet_tasks for Task-to-DWA correlation.

Revision ID: 016_add_onet_task_id
Revises: 015_session_industry
Create Date: 2026-02-05

This migration adds the onet_task_id column which stores O*NET's native Task ID.
This is required to correlate tasks with the Task-to-DWA mapping file from O*NET.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "016_add_onet_task_id"
down_revision: Union[str, None] = "015_session_industry"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add onet_task_id column to onet_tasks."""
    # Add onet_task_id column to store O*NET's native Task ID
    # This field is nullable because tasks imported from other sources
    # may not have O*NET Task IDs
    op.add_column(
        "onet_tasks",
        sa.Column("onet_task_id", sa.Integer(), nullable=True),
    )

    # Create partial unique index for efficient lookup and uniqueness
    # Only enforces uniqueness when onet_task_id is NOT NULL
    # This is the PostgreSQL-recommended way to handle nullable unique columns
    op.execute(
        """
        CREATE UNIQUE INDEX uq_task_onet_id
        ON onet_tasks(occupation_code, onet_task_id)
        WHERE onet_task_id IS NOT NULL
        """
    )

    # Create partial index on onet_task_id for fast lookups
    # Used by get_task_id_mapping() during Task-to-DWA sync
    op.execute(
        """
        CREATE INDEX idx_task_onet_id
        ON onet_tasks(onet_task_id)
        WHERE onet_task_id IS NOT NULL
        """
    )


def downgrade() -> None:
    """Remove onet_task_id column."""
    op.execute("DROP INDEX IF EXISTS idx_task_onet_id")
    op.execute("DROP INDEX IF EXISTS uq_task_onet_id")
    op.drop_column("onet_tasks", "onet_task_id")
