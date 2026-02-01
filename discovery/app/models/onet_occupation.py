"""O*NET Occupation model."""
from datetime import datetime

from sqlalchemy import String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


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

    def __repr__(self) -> str:
        return f"<OnetOccupation(code={self.code}, title={self.title})>"
