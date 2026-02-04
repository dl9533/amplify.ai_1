"""O*NET Occupation model."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.onet_task import OnetTask
    from app.models.onet_occupation_industry import OnetOccupationIndustry


class OnetOccupation(Base):
    """O*NET occupation reference data.

    Stores occupation codes and titles synced from O*NET API.
    Approximately 923 records.
    """

    __tablename__ = "onet_occupations"

    code: Mapped[str] = mapped_column(String(10), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    alternate_titles: Mapped[list["OnetAlternateTitle"]] = relationship(
        back_populates="occupation",
        cascade="all, delete-orphan",
    )
    tasks: Mapped[list["OnetTask"]] = relationship(
        back_populates="occupation",
        cascade="all, delete-orphan",
        foreign_keys="OnetTask.occupation_code",
    )
    industries: Mapped[list["OnetOccupationIndustry"]] = relationship(
        back_populates="occupation",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<OnetOccupation(code={self.code}, title={self.title})>"


class OnetAlternateTitle(Base):
    """Alternate titles for O*NET occupations.

    Maps common job title variations to their canonical O*NET occupation.
    Improves keyword search matching.
    """

    __tablename__ = "onet_alternate_titles"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    onet_code: Mapped[str] = mapped_column(
        String(10),
        ForeignKey("onet_occupations.code", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Relationships
    occupation: Mapped["OnetOccupation"] = relationship(back_populates="alternate_titles")

    def __repr__(self) -> str:
        return f"<OnetAlternateTitle(onet_code={self.onet_code}, title={self.title})>"


class OnetSyncLog(Base):
    """Tracks O*NET database sync history.

    Records when O*NET data was synced, which version, and status.
    Used to determine if sync is needed and for audit purposes.
    """

    __tablename__ = "onet_sync_log"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    occupation_count: Mapped[int] = mapped_column(Integer, nullable=False)
    alternate_title_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    task_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # success, failed

    def __repr__(self) -> str:
        return f"<OnetSyncLog(version={self.version}, status={self.status})>"
