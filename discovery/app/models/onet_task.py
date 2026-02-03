"""O*NET Task models."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.onet_occupation import OnetOccupation


class OnetTask(Base):
    """O*NET tasks (~19,000 records).

    Specific tasks associated with occupations.
    """

    __tablename__ = "onet_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    occupation_code: Mapped[str] = mapped_column(
        String(10),
        ForeignKey("onet_occupations.code", ondelete="CASCADE"),
        nullable=False,
        index=True,
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
    """Junction table linking tasks to DWAs."""
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

    def __repr__(self) -> str:
        return f"<OnetTaskToDWA(task_id={self.task_id}, dwa_id={self.dwa_id})>"
