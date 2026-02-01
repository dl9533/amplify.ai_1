"""Discovery session models for tracking wizard workflow state.

This module provides SQLAlchemy models for the discovery session workflow:
- DiscoverySession: Main session tracking wizard state
- DiscoveryUpload: File upload metadata
- DiscoveryRoleMapping: Maps customer roles to O*NET occupations
- DiscoveryActivitySelection: Selected work activities (DWAs)
- DiscoveryAnalysisResult: Calculated scores per dimension
- AgentificationCandidate: Recommended agents for roadmap
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.modules.discovery.enums import AnalysisDimension, PriorityTier, SessionStatus


class DiscoverySession(Base, TimestampMixin):
    """Discovery session tracking wizard state.

    Represents a discovery workflow session for a user/organization,
    tracking the current step and overall status of the process.
    """

    __tablename__ = "discovery_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    status: Mapped[SessionStatus] = mapped_column(
        String(20), nullable=False, default=SessionStatus.DRAFT
    )
    current_step: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Relationships
    uploads: Mapped[list["DiscoveryUpload"]] = relationship(
        "DiscoveryUpload", back_populates="session", cascade="all, delete-orphan"
    )
    role_mappings: Mapped[list["DiscoveryRoleMapping"]] = relationship(
        "DiscoveryRoleMapping", back_populates="session", cascade="all, delete-orphan"
    )
    activity_selections: Mapped[list["DiscoveryActivitySelection"]] = relationship(
        "DiscoveryActivitySelection",
        back_populates="session",
        cascade="all, delete-orphan",
    )
    analysis_results: Mapped[list["DiscoveryAnalysisResult"]] = relationship(
        "DiscoveryAnalysisResult",
        back_populates="session",
        cascade="all, delete-orphan",
    )
    candidates: Mapped[list["AgentificationCandidate"]] = relationship(
        "AgentificationCandidate",
        back_populates="session",
        cascade="all, delete-orphan",
    )


class DiscoveryUpload(Base, TimestampMixin):
    """Discovery upload storing file metadata.

    Tracks uploaded files with their metadata including detected schema
    and column mappings for parsing.
    """

    __tablename__ = "discovery_uploads"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("discovery_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    column_mappings: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    detected_schema: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Relationships
    session: Mapped["DiscoverySession"] = relationship(
        "DiscoverySession", back_populates="uploads"
    )


class DiscoveryRoleMapping(Base, TimestampMixin):
    """Discovery role mapping linking customer roles to O*NET occupations.

    Maps a source role from the customer's data to an O*NET occupation code,
    with confidence scores and user confirmation tracking.
    """

    __tablename__ = "discovery_role_mappings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("discovery_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_role: Mapped[str] = mapped_column(String(255), nullable=False)
    onet_code: Mapped[str | None] = mapped_column(
        String(12), ForeignKey("onet_occupations.code"), nullable=True, index=True
    )
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    user_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships
    session: Mapped["DiscoverySession"] = relationship(
        "DiscoverySession", back_populates="role_mappings"
    )
    activity_selections: Mapped[list["DiscoveryActivitySelection"]] = relationship(
        "DiscoveryActivitySelection",
        back_populates="role_mapping",
        cascade="all, delete-orphan",
    )
    analysis_results: Mapped[list["DiscoveryAnalysisResult"]] = relationship(
        "DiscoveryAnalysisResult",
        back_populates="role_mapping",
        cascade="all, delete-orphan",
    )
    candidates: Mapped[list["AgentificationCandidate"]] = relationship(
        "AgentificationCandidate",
        back_populates="role_mapping",
        cascade="all, delete-orphan",
    )


class DiscoveryActivitySelection(Base, TimestampMixin):
    """Discovery activity selection tracking DWA selections.

    Tracks which Detailed Work Activities (DWAs) have been selected
    for a role mapping, with user modification tracking.
    """

    __tablename__ = "discovery_activity_selections"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("discovery_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role_mapping_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("discovery_role_mappings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dwa_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("onet_dwas.id"), nullable=False, index=True
    )
    selected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    user_modified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    session: Mapped["DiscoverySession"] = relationship(
        "DiscoverySession", back_populates="activity_selections"
    )
    role_mapping: Mapped["DiscoveryRoleMapping"] = relationship(
        "DiscoveryRoleMapping", back_populates="activity_selections"
    )


class DiscoveryAnalysisResult(Base, TimestampMixin):
    """Discovery analysis result storing scores.

    Stores calculated scores for a role mapping along a specific dimension,
    including AI exposure, impact, complexity, and priority scores.
    """

    __tablename__ = "discovery_analysis_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("discovery_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role_mapping_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("discovery_role_mappings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dimension: Mapped[AnalysisDimension] = mapped_column(String(20), nullable=False)
    dimension_value: Mapped[str] = mapped_column(String(255), nullable=False)
    ai_exposure_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    impact_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    complexity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    priority_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    breakdown: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Relationships
    session: Mapped["DiscoverySession"] = relationship(
        "DiscoverySession", back_populates="analysis_results"
    )
    role_mapping: Mapped["DiscoveryRoleMapping"] = relationship(
        "DiscoveryRoleMapping", back_populates="analysis_results"
    )


class AgentificationCandidate(Base, TimestampMixin):
    """Agentification candidate tracking roadmap items.

    Represents a recommended agent that could be built based on the
    discovery analysis, with priority tier and impact estimates.
    """

    __tablename__ = "agentification_candidates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("discovery_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role_mapping_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("discovery_role_mappings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority_tier: Mapped[PriorityTier] = mapped_column(String(20), nullable=False)
    estimated_impact: Mapped[float | None] = mapped_column(Float, nullable=True)
    selected_for_build: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    intake_request_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # Relationships
    session: Mapped["DiscoverySession"] = relationship(
        "DiscoverySession", back_populates="candidates"
    )
    role_mapping: Mapped["DiscoveryRoleMapping"] = relationship(
        "DiscoveryRoleMapping", back_populates="candidates"
    )
