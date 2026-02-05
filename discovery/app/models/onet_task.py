"""O*NET Task models."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.onet_occupation import OnetOccupation
    from app.models.onet_work_activities import OnetDWA


class OnetTask(Base):
    """O*NET tasks (~19,000 records).

    Specific tasks associated with occupations. Each task has a unique
    onet_task_id within its occupation, which is used to correlate with
    the Task-to-DWA mapping from O*NET.

    Note: onet_task_id is populated from O*NET's Task Statements file during
    sync. This field is required for Task-to-DWA correlation. Tasks without
    onet_task_id cannot be linked to DWAs for AI impact analysis.
    """

    __tablename__ = "onet_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    occupation_code: Mapped[str] = mapped_column(
        String(10),
        ForeignKey("onet_occupations.code", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    onet_task_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        doc="O*NET's native Task ID for correlation with Task-to-DWA mapping",
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    importance: Mapped[float | None] = mapped_column(Float, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    occupation: Mapped["OnetOccupation"] = relationship(
        back_populates="tasks",
        foreign_keys=[occupation_code],
    )
    dwas: Mapped[list["OnetTaskToDWA"]] = relationship(back_populates="task", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<OnetTask(id={self.id}, occupation_code={self.occupation_code})>"


class OnetTaskToDWA(Base):
    """Junction table linking tasks to DWAs.

    This mapping comes from O*NET's "Tasks to DWAs.txt" file and enables
    the Task → DWA → IWA → GWA hierarchy for AI impact analysis.
    """
    __tablename__ = "onet_task_to_dwa"

    task_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("onet_tasks.id", ondelete="CASCADE"),
        primary_key=True,
    )
    dwa_id: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("onet_dwa.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # Relationships
    task: Mapped["OnetTask"] = relationship(back_populates="dwas")
    dwa: Mapped["OnetDWA"] = relationship()

    def __repr__(self) -> str:
        return f"<OnetTaskToDWA(task_id={self.task_id}, dwa_id={self.dwa_id})>"
