"""Discovery session enums for status, analysis dimensions, and priority tiers."""

from enum import Enum


class SessionStatus(str, Enum):
    """Discovery session lifecycle states."""

    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class AnalysisDimension(str, Enum):
    """Discovery analysis view dimensions."""

    ROLE = "role"
    TASK = "task"
    LOB = "lob"
    GEOGRAPHY = "geography"
    DEPARTMENT = "department"


class PriorityTier(str, Enum):
    """Roadmap timeline buckets for opportunity prioritization."""

    NOW = "now"
    NEXT_QUARTER = "next_quarter"
    FUTURE = "future"
