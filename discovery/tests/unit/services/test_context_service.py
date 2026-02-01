# tests/unit/services/test_context_service.py
import pytest
from uuid import uuid4

from app.services.context_service import ContextService


@pytest.fixture
def context_service():
    return ContextService()


def test_build_context_includes_current_step(context_service):
    """Context should include current step information."""
    session_id = uuid4()
    context = context_service.build_context(
        session_id=session_id,
        current_step=2,
        user_message="What should I do next?"
    )

    assert context["current_step"] == 2
    assert context["step_name"] == "Map Roles"


def test_build_context_includes_step_data(context_service):
    """Context should include relevant data for current step."""
    session_id = uuid4()
    context = context_service.build_context(
        session_id=session_id,
        current_step=3,
        user_message="Which activities are most important?"
    )

    assert "activities" in context
    assert "gwa_groups" in context["activities"]


def test_context_includes_selection_counts(context_service):
    """Context should include selection counts."""
    session_id = uuid4()
    context = context_service.build_context(
        session_id=session_id,
        current_step=3,
        user_message="How many have I selected?"
    )

    assert "selection_count" in context


def test_context_includes_analysis_summary(context_service):
    """Context should include analysis summary when on step 4+."""
    session_id = uuid4()
    context = context_service.build_context(
        session_id=session_id,
        current_step=4,
        user_message="Show me the top priorities"
    )

    assert "analysis_summary" in context
    assert "top_priorities" in context["analysis_summary"]


def test_suggests_quick_actions_based_on_context(context_service):
    """Should suggest relevant quick actions."""
    session_id = uuid4()
    context = context_service.build_context(
        session_id=session_id,
        current_step=2,
        user_message="I'm not sure about this mapping"
    )

    assert "suggested_actions" in context
    assert any("remap" in a["action"] for a in context["suggested_actions"])
