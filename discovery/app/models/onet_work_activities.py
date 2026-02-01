"""O*NET Work Activity models (GWA, IWA, DWA hierarchy)."""
from datetime import datetime, timezone

from sqlalchemy import String, Text, DateTime, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class OnetGWA(Base):
    """Generalized Work Activities (41 records).

    Top level of work activity hierarchy.
    Contains AI exposure scores from Pew Research mapping.
    """
    __tablename__ = "onet_gwa"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_exposure_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    iwas: Mapped[list["OnetIWA"]] = relationship(back_populates="gwa")


class OnetIWA(Base):
    """Intermediate Work Activities (~300 records).

    Middle level of work activity hierarchy.
    """
    __tablename__ = "onet_iwa"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    gwa_id: Mapped[str] = mapped_column(String(20), ForeignKey("onet_gwa.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    gwa: Mapped["OnetGWA"] = relationship(back_populates="iwas")
    dwas: Mapped[list["OnetDWA"]] = relationship(back_populates="iwa")


class OnetDWA(Base):
    """Detailed Work Activities (2000+ records).

    Lowest level of work activity hierarchy.
    AI exposure inherited from GWA unless overridden.
    """
    __tablename__ = "onet_dwa"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    iwa_id: Mapped[str] = mapped_column(String(20), ForeignKey("onet_iwa.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_exposure_override: Mapped[float | None] = mapped_column(Float, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    iwa: Mapped["OnetIWA"] = relationship(back_populates="dwas")
