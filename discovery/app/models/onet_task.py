"""O*NET Task models."""
from datetime import datetime, timezone

from sqlalchemy import String, Text, DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class OnetTask(Base):
    """O*NET tasks (~19,000 records).

    Specific tasks associated with occupations.
    """
    __tablename__ = "onet_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    occupation_code: Mapped[str] = mapped_column(
        String(10),
        ForeignKey("onet_occupations.code"),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    importance: Mapped[float | None] = mapped_column(Float, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    dwas: Mapped[list["OnetTaskToDWA"]] = relationship(back_populates="task")


class OnetTaskToDWA(Base):
    """Junction table linking tasks to DWAs."""
    __tablename__ = "onet_task_to_dwa"

    task_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("onet_tasks.id"),
        primary_key=True,
    )
    dwa_id: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("onet_dwa.id"),
        primary_key=True,
    )

    # Relationships
    task: Mapped["OnetTask"] = relationship(back_populates="dwas")
