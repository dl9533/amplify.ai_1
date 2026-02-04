"""O*NET occupation-industry mapping model."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.onet_occupation import OnetOccupation


class OnetOccupationIndustry(Base):
    """Maps O*NET occupations to industries where they're employed.

    Sourced from O*NET Industry.txt file, which provides industry distribution
    data for each occupation. Used to boost occupation matches when the user's
    LOB aligns with industries where the occupation is commonly found.

    employment_percent indicates what percentage of workers in this occupation
    are employed in this industry.
    """

    __tablename__ = "onet_occupation_industries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    occupation_code: Mapped[str] = mapped_column(
        String(10),
        ForeignKey("onet_occupations.code", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    naics_code: Mapped[str] = mapped_column(String(6), nullable=False, index=True)
    naics_title: Mapped[str] = mapped_column(String(255), nullable=False)
    employment_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationship to occupation
    occupation: Mapped["OnetOccupation"] = relationship(back_populates="industries")

    def __repr__(self) -> str:
        return f"<OnetOccupationIndustry(occ={self.occupation_code}, naics={self.naics_code})>"
