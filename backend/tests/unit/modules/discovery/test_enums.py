import pytest

from app.modules.discovery.enums import (
    SessionStatus,
    AnalysisDimension,
    PriorityTier,
)


def test_session_status_enum():
    """SessionStatus should track discovery session lifecycle."""
    assert SessionStatus.DRAFT.value == "draft"
    assert SessionStatus.IN_PROGRESS.value == "in_progress"
    assert SessionStatus.COMPLETED.value == "completed"
    assert SessionStatus.ARCHIVED.value == "archived"


def test_analysis_dimension_enum():
    """AnalysisDimension should define 5 view dimensions."""
    assert AnalysisDimension.ROLE.value == "role"
    assert AnalysisDimension.TASK.value == "task"
    assert AnalysisDimension.LOB.value == "lob"
    assert AnalysisDimension.GEOGRAPHY.value == "geography"
    assert AnalysisDimension.DEPARTMENT.value == "department"


def test_priority_tier_enum():
    """PriorityTier should define roadmap timeline buckets."""
    assert PriorityTier.NOW.value == "now"
    assert PriorityTier.NEXT_QUARTER.value == "next_quarter"
    assert PriorityTier.FUTURE.value == "future"
