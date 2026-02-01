"""O*NET Skills models."""
from datetime import datetime, timezone

from sqlalchemy import String, Text, DateTime, Boolean, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class OnetSkill(Base):
    """O*NET skills reference data."""
    __tablename__ = "onet_skills"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


class OnetTechnologySkill(Base):
    """O*NET technology skills by occupation."""
    __tablename__ = "onet_technology_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    occupation_code: Mapped[str] = mapped_column(
        String(10),
        ForeignKey("onet_occupations.code"),
        nullable=False,
    )
    technology_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hot_technology: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
