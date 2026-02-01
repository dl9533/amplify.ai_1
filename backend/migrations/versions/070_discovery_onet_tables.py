"""O*NET tables migration - creates tables for occupation and work activity data.

This migration creates the O*NET database tables for storing occupation data,
work activities (GWA/IWA/DWA hierarchy), tasks, skills, and technology skills.

O*NET Work Activity Hierarchy:
- GWA (Generalized Work Activity): Top-level categories
- IWA (Intermediate Work Activity): Mid-level activities under GWA
- DWA (Detailed Work Activity): Specific detailed tasks under IWA

Revision ID: 070_discovery_onet_tables
Revises: 103_pipeline_module
Create Date: 2026-01-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "070_discovery_onet_tables"
down_revision: str | None = "103_pipeline_module"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create O*NET tables with all required columns, indexes, and foreign keys."""
    # Create onet_occupations table
    op.create_table(
        "onet_occupations",
        sa.Column("code", sa.String(12), primary_key=True),  # e.g., "15-1252.00"
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
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

    # Create onet_gwas table (Generalized Work Activities)
    op.create_table(
        "onet_gwas",
        sa.Column("id", sa.String(20), primary_key=True),  # e.g., "4.A.1.a.1"
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("ai_exposure_score", sa.Float(), nullable=True),  # 0.0-1.0
    )

    # Create onet_iwas table (Intermediate Work Activities)
    op.create_table(
        "onet_iwas",
        sa.Column("id", sa.String(20), primary_key=True),
        sa.Column(
            "gwa_id",
            sa.String(20),
            sa.ForeignKey("onet_gwas.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
    )

    # Create index for gwa_id on onet_iwas
    op.create_index("ix_onet_iwas_gwa_id", "onet_iwas", ["gwa_id"])

    # Create onet_dwas table (Detailed Work Activities)
    op.create_table(
        "onet_dwas",
        sa.Column("id", sa.String(20), primary_key=True),
        sa.Column(
            "iwa_id",
            sa.String(20),
            sa.ForeignKey("onet_iwas.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "ai_exposure_override", sa.Float(), nullable=True
        ),  # NULL = inherit from GWA
    )

    # Create index for iwa_id on onet_dwas
    op.create_index("ix_onet_dwas_iwa_id", "onet_dwas", ["iwa_id"])

    # Create onet_tasks table
    op.create_table(
        "onet_tasks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "occupation_code",
            sa.String(12),
            sa.ForeignKey("onet_occupations.code", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("importance", sa.Float(), nullable=True),
    )

    # Create index for occupation_code on onet_tasks
    op.create_index("ix_onet_tasks_occupation_code", "onet_tasks", ["occupation_code"])

    # Create onet_skills table
    op.create_table(
        "onet_skills",
        sa.Column("id", sa.String(20), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
    )

    # Create onet_technology_skills table
    op.create_table(
        "onet_technology_skills",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "occupation_code",
            sa.String(12),
            sa.ForeignKey("onet_occupations.code", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("technology_name", sa.String(255), nullable=False),
        sa.Column(
            "hot_technology", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
    )

    # Create index for occupation_code on onet_technology_skills
    op.create_index(
        "ix_onet_technology_skills_occupation_code",
        "onet_technology_skills",
        ["occupation_code"],
    )


def downgrade() -> None:
    """Drop all O*NET tables in reverse order of creation."""
    # Drop indexes first
    op.drop_index(
        "ix_onet_technology_skills_occupation_code",
        table_name="onet_technology_skills",
    )
    op.drop_index("ix_onet_tasks_occupation_code", table_name="onet_tasks")
    op.drop_index("ix_onet_dwas_iwa_id", table_name="onet_dwas")
    op.drop_index("ix_onet_iwas_gwa_id", table_name="onet_iwas")

    # Drop tables in reverse order (respecting foreign key dependencies)
    op.drop_table("onet_technology_skills")
    op.drop_table("onet_skills")
    op.drop_table("onet_tasks")
    op.drop_table("onet_dwas")
    op.drop_table("onet_iwas")
    op.drop_table("onet_gwas")
    op.drop_table("onet_occupations")
