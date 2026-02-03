"""Create O*NET tasks and technology skills tables.

Revision ID: 003_tasks_skills
Revises: 002_work_activities
Create Date: 2026-02-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "003_tasks_skills"
down_revision: Union[str, None] = "002_work_activities"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create onet_tasks table
    op.create_table(
        "onet_tasks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("occupation_code", sa.String(10), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("importance", sa.Float(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["occupation_code"],
            ["onet_occupations.code"],
            ondelete="CASCADE",
        ),
    )
    op.create_index("idx_task_occupation", "onet_tasks", ["occupation_code"])

    # Create onet_technology_skills table
    op.create_table(
        "onet_technology_skills",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("occupation_code", sa.String(10), nullable=False),
        sa.Column("technology_name", sa.String(255), nullable=False),
        sa.Column("hot_technology", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["occupation_code"],
            ["onet_occupations.code"],
            ondelete="CASCADE",
        ),
    )
    op.create_index("idx_tech_skill_occupation", "onet_technology_skills", ["occupation_code"])

    # Create onet_task_to_dwa junction table
    op.create_table(
        "onet_task_to_dwa",
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("dwa_id", sa.String(20), nullable=False),
        sa.PrimaryKeyConstraint("task_id", "dwa_id"),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["onet_tasks.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["dwa_id"],
            ["onet_dwa.id"],
            ondelete="CASCADE",
        ),
    )


def downgrade() -> None:
    op.drop_table("onet_task_to_dwa")

    op.drop_index("idx_tech_skill_occupation", table_name="onet_technology_skills")
    op.drop_table("onet_technology_skills")

    op.drop_index("idx_task_occupation", table_name="onet_tasks")
    op.drop_table("onet_tasks")
