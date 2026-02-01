"""Discovery analysis results model."""
import enum
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import String, DateTime, Float, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AnalysisDimension(enum.Enum):
    """Dimension for analysis grouping."""
    ROLE = "role"
    TASK = "task"
    LOB = "lob"
    GEOGRAPHY = "geography"
    DEPARTMENT = "department"


class DiscoveryAnalysisResult(Base):
    """AI exposure and impact analysis results."""
    __tablename__ = "discovery_analysis_results"

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
    role_mapping_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("discovery_role_mappings.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    dimension: Mapped[AnalysisDimension] = mapped_column(
        Enum(AnalysisDimension),
        nullable=False,
    )
    dimension_value: Mapped[str] = mapped_column(String(255), nullable=False)
    ai_exposure_score: Mapped[float] = mapped_column(Float, nullable=False)
    impact_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    complexity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    priority_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    breakdown: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        return f"<DiscoveryAnalysisResult(id={self.id}, dimension={self.dimension.value}, score={self.ai_exposure_score})>"
