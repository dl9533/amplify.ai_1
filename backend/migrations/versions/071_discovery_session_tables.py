"""Discovery session tables migration.

Creates tables for the discovery wizard workflow:
- discovery_sessions: Main session tracking wizard state
- discovery_uploads: File upload metadata
- discovery_role_mappings: Maps customer roles to O*NET occupations
- discovery_activity_selections: Selected work activities (DWAs)
- discovery_analysis_results: Calculated scores per dimension
- agentification_candidates: Recommended agents for roadmap

Revision ID: 071_discovery_session_tables
Revises: 070_discovery_onet_tables
Create Date: 2026-01-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "071_discovery_session_tables"
down_revision: str | None = "070_discovery_onet_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create discovery session tables with all required columns, indexes, and foreign keys."""
    # Create discovery_sessions table
    op.create_table(
        "discovery_sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column(
            "organization_id", postgresql.UUID(as_uuid=True), nullable=False, index=True
        ),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("current_step", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )

    # Create discovery_uploads table
    op.create_table(
        "discovery_uploads",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("discovery_sessions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("file_url", sa.String(1024), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=True),
        sa.Column("column_mappings", postgresql.JSON(), nullable=True),
        sa.Column("detected_schema", postgresql.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )

    # Create discovery_role_mappings table
    op.create_table(
        "discovery_role_mappings",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("discovery_sessions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("source_role", sa.String(255), nullable=False),
        sa.Column(
            "onet_code",
            sa.String(12),
            sa.ForeignKey("onet_occupations.code"),
            nullable=True,
            index=True,
        ),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column(
            "user_confirmed", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column("row_count", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )

    # Create discovery_activity_selections table
    op.create_table(
        "discovery_activity_selections",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("discovery_sessions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "role_mapping_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("discovery_role_mappings.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "dwa_id",
            sa.String(20),
            sa.ForeignKey("onet_dwas.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "selected", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column(
            "user_modified", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )

    # Create discovery_analysis_results table
    op.create_table(
        "discovery_analysis_results",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("discovery_sessions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "role_mapping_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("discovery_role_mappings.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("dimension", sa.String(20), nullable=False),
        sa.Column("dimension_value", sa.String(255), nullable=False),
        sa.Column("ai_exposure_score", sa.Float(), nullable=True),
        sa.Column("impact_score", sa.Float(), nullable=True),
        sa.Column("complexity_score", sa.Float(), nullable=True),
        sa.Column("priority_score", sa.Float(), nullable=True),
        sa.Column("breakdown", postgresql.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )

    # Create agentification_candidates table
    op.create_table(
        "agentification_candidates",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("discovery_sessions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "role_mapping_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("discovery_role_mappings.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("priority_tier", sa.String(20), nullable=False),
        sa.Column("estimated_impact", sa.Float(), nullable=True),
        sa.Column(
            "selected_for_build",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("intake_request_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Drop all discovery session tables in reverse order of creation."""
    # Drop tables in reverse order (respecting foreign key dependencies)
    op.drop_table("agentification_candidates")
    op.drop_table("discovery_analysis_results")
    op.drop_table("discovery_activity_selections")
    op.drop_table("discovery_role_mappings")
    op.drop_table("discovery_uploads")
    op.drop_table("discovery_sessions")
