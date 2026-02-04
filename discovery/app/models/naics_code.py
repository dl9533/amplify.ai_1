"""NAICS code reference model."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class NaicsCode(Base):
    """North American Industry Classification System reference data.

    Hierarchical industry classification codes from the Census Bureau.
    Used to map Lines of Business to industry sectors for occupation matching.

    Levels:
    - 2-digit: Sector (e.g., 52 = Finance and Insurance)
    - 3-digit: Subsector (e.g., 522 = Credit Intermediation)
    - 4-digit: Industry Group (e.g., 5221 = Depository Credit Intermediation)
    - 5-digit: NAICS Industry (e.g., 52211 = Commercial Banking)
    - 6-digit: National Industry (e.g., 522110 = Commercial Banking)
    """

    __tablename__ = "naics_codes"

    code: Mapped[str] = mapped_column(String(6), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    parent_code: Mapped[str | None] = mapped_column(
        String(6),
        ForeignKey("naics_codes.code"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Self-referential relationship for hierarchy
    parent: Mapped["NaicsCode | None"] = relationship(
        "NaicsCode",
        remote_side=[code],
        backref="children",
    )

    def __repr__(self) -> str:
        return f"<NaicsCode(code={self.code}, title={self.title})>"
