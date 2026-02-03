"""Create base enums and core tables.

Revision ID: 000_enums_base
Revises:
Create Date: 2026-02-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "000_enums_base"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    discovery_status_enum = postgresql.ENUM(
        "pending",
        "upload_complete",
        "mapping_complete",
        "analysis_complete",
        "finalized",
        name="discovery_status",
        create_type=False,
    )
    discovery_status_enum.create(op.get_bind(), checkfirst=True)

    analysis_dimension_enum = postgresql.ENUM(
        "role",
        "task",
        "lob",
        "geography",
        "department",
        name="analysis_dimension",
        create_type=False,
    )
    analysis_dimension_enum.create(op.get_bind(), checkfirst=True)

    priority_tier_enum = postgresql.ENUM(
        "now",
        "next_quarter",
        "future",
        name="priority_tier",
        create_type=False,
    )
    priority_tier_enum.create(op.get_bind(), checkfirst=True)

    # Create onet_occupations table
    op.create_table(
        "onet_occupations",
        sa.Column("code", sa.String(10), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("code"),
    )

    # Full-text search index on occupations
    op.execute("""
        CREATE INDEX idx_onet_occupation_search
        ON onet_occupations
        USING gin(to_tsvector('english', title || ' ' || COALESCE(description, '')))
    """)

    # Create onet_gwa table (Generalized Work Activities)
    op.create_table(
        "onet_gwa",
        sa.Column("id", sa.String(20), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("ai_exposure_score", sa.Float(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_gwa_ai_exposure", "onet_gwa", ["ai_exposure_score"])

    # Create onet_skills table
    op.create_table(
        "onet_skills",
        sa.Column("id", sa.String(20), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create discovery_sessions table
    op.create_table(
        "discovery_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending",
                "upload_complete",
                "mapping_complete",
                "analysis_complete",
                "finalized",
                name="discovery_status",
                create_type=False,
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("current_step", sa.String(50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_session_user", "discovery_sessions", ["user_id"])
    op.create_index("idx_session_org", "discovery_sessions", ["organization_id"])
    op.create_index("idx_session_status", "discovery_sessions", ["status"])


def downgrade() -> None:
    op.drop_index("idx_session_status", table_name="discovery_sessions")
    op.drop_index("idx_session_org", table_name="discovery_sessions")
    op.drop_index("idx_session_user", table_name="discovery_sessions")
    op.drop_table("discovery_sessions")

    op.drop_table("onet_skills")

    op.drop_index("idx_gwa_ai_exposure", table_name="onet_gwa")
    op.drop_table("onet_gwa")

    op.drop_index("idx_onet_occupation_search", table_name="onet_occupations")
    op.drop_table("onet_occupations")

    # Drop enum types
    postgresql.ENUM(name="priority_tier").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="analysis_dimension").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="discovery_status").drop(op.get_bind(), checkfirst=True)
