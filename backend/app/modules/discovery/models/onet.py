"""O*NET data models for occupation and work activity hierarchies.

This module provides SQLAlchemy models for storing O*NET (Occupational Information
Network) data, including occupations, work activities (GWA/IWA/DWA hierarchy),
tasks, skills, and technology skills.

O*NET Work Activity Hierarchy:
- GWA (Generalized Work Activity): Top-level categories (e.g., "Getting Information")
- IWA (Intermediate Work Activity): Mid-level activities (e.g., "Communicating with supervisors")
- DWA (Detailed Work Activity): Specific detailed tasks

The ai_exposure_score on GWA represents the Pew Research AI exposure metric (0.0-1.0).
DWA can optionally override this with ai_exposure_override.
"""

from datetime import datetime

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class OnetOccupation(Base, TimestampMixin):
    """O*NET occupation record.

    Represents a standard occupation as defined by O*NET, identified by
    a SOC code (e.g., "15-1252.00" for Software Developers).
    """

    __tablename__ = "onet_occupations"

    code: Mapped[str] = mapped_column(
        String(12), primary_key=True
    )  # e.g., "15-1252.00"
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    tasks: Mapped[list["OnetTask"]] = relationship(
        "OnetTask", back_populates="occupation"
    )
    technology_skills: Mapped[list["OnetTechnologySkill"]] = relationship(
        "OnetTechnologySkill", back_populates="occupation"
    )


class OnetGwa(Base):
    """Generalized Work Activity (GWA).

    Top-level work activity categories in the O*NET hierarchy.
    Examples: "Getting Information", "Making Decisions and Solving Problems"

    The ai_exposure_score is the Pew Research AI exposure metric (0.0-1.0)
    indicating how susceptible this work activity is to AI automation.
    """

    __tablename__ = "onet_gwas"

    id: Mapped[str] = mapped_column(
        String(20), primary_key=True
    )  # e.g., "4.A.1.a.1"
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_exposure_score: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )  # 0.0-1.0

    # Relationships
    iwas: Mapped[list["OnetIwa"]] = relationship("OnetIwa", back_populates="gwa")


class OnetIwa(Base):
    """Intermediate Work Activity (IWA).

    Mid-level work activities that belong to a GWA.
    Examples: "Communicating with supervisors", "Scheduling work"
    """

    __tablename__ = "onet_iwas"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    gwa_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("onet_gwas.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    gwa: Mapped["OnetGwa"] = relationship("OnetGwa", back_populates="iwas")
    dwas: Mapped[list["OnetDwa"]] = relationship("OnetDwa", back_populates="iwa")


class OnetDwa(Base):
    """Detailed Work Activity (DWA).

    Specific detailed tasks that belong to an IWA.
    The ai_exposure_override allows overriding the parent GWA's AI exposure
    score for this specific activity. NULL means inherit from GWA.
    """

    __tablename__ = "onet_dwas"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    iwa_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("onet_iwas.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_exposure_override: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )  # NULL = inherit from GWA

    # Relationships
    iwa: Mapped["OnetIwa"] = relationship("OnetIwa", back_populates="dwas")


class OnetTask(Base):
    """O*NET occupation task.

    Specific tasks associated with an occupation, with importance scores.
    """

    __tablename__ = "onet_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    occupation_code: Mapped[str] = mapped_column(
        String(12), ForeignKey("onet_occupations.code"), nullable=False, index=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    importance: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    occupation: Mapped["OnetOccupation"] = relationship(
        "OnetOccupation", back_populates="tasks"
    )


class OnetSkill(Base):
    """O*NET skill definition.

    Standard skills tracked by O*NET (e.g., "Critical Thinking", "Programming").
    """

    __tablename__ = "onet_skills"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class OnetTechnologySkill(Base):
    """O*NET technology skill for an occupation.

    Technology tools and software associated with an occupation.
    hot_technology indicates if this is a frequently listed or in-demand technology.
    """

    __tablename__ = "onet_technology_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    occupation_code: Mapped[str] = mapped_column(
        String(12), ForeignKey("onet_occupations.code"), nullable=False, index=True
    )
    technology_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hot_technology: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    occupation: Mapped["OnetOccupation"] = relationship(
        "OnetOccupation", back_populates="technology_skills"
    )
