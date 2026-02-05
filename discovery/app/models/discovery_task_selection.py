"""Discovery task selection model.

User selections of O*NET tasks for AI impact analysis.
"""
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class DiscoveryTaskSelection(Base):
    """User selections of tasks for analysis.

    Stores which O*NET tasks the user has selected for each role mapping.
    Selected tasks are used to calculate AI exposure scores through the
    Task → DWA → IWA → GWA hierarchy.
    """
    __tablename__ = "discovery_task_selections"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    session_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("discovery_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role_mapping_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("discovery_role_mappings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    task_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("onet_tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    selected: Mapped[bool] = mapped_column(Boolean, default=True)
    user_modified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    role_mapping: Mapped["DiscoveryRoleMapping"] = relationship(
        back_populates="task_selections"
    )
    task: Mapped["OnetTask"] = relationship()

    def __repr__(self) -> str:
        return f"<DiscoveryTaskSelection(id={self.id}, task_id={self.task_id}, selected={self.selected})>"
