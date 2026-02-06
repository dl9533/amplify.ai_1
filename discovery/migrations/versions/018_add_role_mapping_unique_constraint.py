"""Add unique constraint to prevent duplicate role mappings.

Revision ID: 018_role_mapping_unique
Revises: 017_discovery_task_selections
Create Date: 2026-02-05
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "018_role_mapping_unique"
down_revision: Union[str, None] = "017_task_selections"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add unique constraint on (session_id, source_role, lob_value).

    This prevents duplicate role mappings within the same LOB for a session.
    Note: lob_value can be NULL, and PostgreSQL treats NULL values as distinct,
    so we use COALESCE to handle NULL LOB values consistently.
    """
    # Create unique index that handles NULL lob_value
    # PostgreSQL unique indexes treat NULLs as distinct, so we use COALESCE
    op.execute("""
        CREATE UNIQUE INDEX uq_role_mapping_session_role_lob
        ON discovery_role_mappings (session_id, source_role, COALESCE(lob_value, ''))
    """)


def downgrade() -> None:
    """Remove the unique constraint."""
    op.execute("DROP INDEX IF EXISTS uq_role_mapping_session_role_lob")
