# tests/unit/services/test_context_service.py
import pytest
from uuid import uuid4

from app.services.context_service import ContextService


@pytest.fixture
def context_service():
    return ContextService()


@pytest.mark.asyncio
async def test_build_context_includes_current_step(context_service):
    """Context should include current step information."""
    session_id = uuid4()
    context = await context_service.build_context(
        session_id=session_id,
        current_step=2,
        user_message="What should I do next?"
    )

    assert context["current_step"] == 2
    assert context["step_name"] == "Map Roles"


@pytest.mark.asyncio
async def test_build_context_includes_step_data(context_service):
    """Context should include relevant data for current step."""
    session_id = uuid4()
    context = await context_service.build_context(
        session_id=session_id,
        current_step=3,
        user_message="Which activities are most important?"
    )

    assert "activities" in context
    assert "gwa_groups" in context["activities"]


@pytest.mark.asyncio
async def test_context_includes_selection_counts(context_service):
    """Context should include selection counts."""
    session_id = uuid4()
    context = await context_service.build_context(
        session_id=session_id,
        current_step=3,
        user_message="How many have I selected?"
    )

    assert "selection_count" in context


@pytest.mark.asyncio
async def test_context_includes_analysis_summary(context_service):
    """Context should include analysis summary when on step 4+."""
    session_id = uuid4()
    context = await context_service.build_context(
        session_id=session_id,
        current_step=4,
        user_message="Show me the top priorities"
    )

    assert "analysis_summary" in context
    assert "top_priorities" in context["analysis_summary"]


@pytest.mark.asyncio
async def test_suggests_quick_actions_based_on_context(context_service):
    """Should suggest relevant quick actions."""
    session_id = uuid4()
    context = await context_service.build_context(
        session_id=session_id,
        current_step=2,
        user_message="I'm not sure about this mapping"
    )

    assert "suggested_actions" in context
    assert any("remap" in a["action"] for a in context["suggested_actions"])


# === Input Validation Tests ===

class TestCurrentStepValidation:
    """Tests for current_step parameter validation."""

    @pytest.mark.asyncio
    async def test_current_step_zero_raises_value_error(self, context_service):
        """Step 0 should raise ValueError."""
        session_id = uuid4()
        with pytest.raises(ValueError, match="current_step must be between 1 and 5"):
            await context_service.build_context(
                session_id=session_id,
                current_step=0,
                user_message="Test message"
            )

    @pytest.mark.asyncio
    async def test_current_step_negative_raises_value_error(self, context_service):
        """Negative step should raise ValueError."""
        session_id = uuid4()
        with pytest.raises(ValueError, match="current_step must be between 1 and 5"):
            await context_service.build_context(
                session_id=session_id,
                current_step=-1,
                user_message="Test message"
            )

    @pytest.mark.asyncio
    async def test_current_step_six_raises_value_error(self, context_service):
        """Step 6 should raise ValueError."""
        session_id = uuid4()
        with pytest.raises(ValueError, match="current_step must be between 1 and 5"):
            await context_service.build_context(
                session_id=session_id,
                current_step=6,
                user_message="Test message"
            )

    @pytest.mark.asyncio
    async def test_current_step_large_number_raises_value_error(self, context_service):
        """Large step number should raise ValueError."""
        session_id = uuid4()
        with pytest.raises(ValueError, match="current_step must be between 1 and 5"):
            await context_service.build_context(
                session_id=session_id,
                current_step=100,
                user_message="Test message"
            )


class TestUserMessageValidation:
    """Tests for user_message parameter validation."""

    @pytest.mark.asyncio
    async def test_oversized_message_raises_value_error(self, context_service):
        """Message exceeding 10000 characters should raise ValueError."""
        session_id = uuid4()
        oversized_message = "a" * 10001
        with pytest.raises(ValueError, match="user_message exceeds maximum length"):
            await context_service.build_context(
                session_id=session_id,
                current_step=1,
                user_message=oversized_message
            )

    @pytest.mark.asyncio
    async def test_message_at_max_length_is_valid(self, context_service):
        """Message at exactly 10000 characters should be valid."""
        session_id = uuid4()
        max_message = "a" * 10000
        context = await context_service.build_context(
            session_id=session_id,
            current_step=1,
            user_message=max_message
        )
        assert context["current_step"] == 1


class TestBoundaryConditions:
    """Tests for boundary conditions (step 1 and step 5)."""

    @pytest.mark.asyncio
    async def test_step_one_is_valid_boundary(self, context_service):
        """Step 1 should be valid (lower boundary)."""
        session_id = uuid4()
        context = await context_service.build_context(
            session_id=session_id,
            current_step=1,
            user_message="Test message"
        )
        assert context["current_step"] == 1
        assert context["step_name"] == "Upload"

    @pytest.mark.asyncio
    async def test_step_five_is_valid_boundary(self, context_service):
        """Step 5 should be valid (upper boundary)."""
        session_id = uuid4()
        context = await context_service.build_context(
            session_id=session_id,
            current_step=5,
            user_message="Test message"
        )
        assert context["current_step"] == 5
        assert context["step_name"] == "Roadmap"

    @pytest.mark.asyncio
    async def test_step_five_includes_analysis_summary(self, context_service):
        """Step 5 should include analysis summary (step >= 4)."""
        session_id = uuid4()
        context = await context_service.build_context(
            session_id=session_id,
            current_step=5,
            user_message="Test message"
        )
        assert "analysis_summary" in context

    @pytest.mark.asyncio
    async def test_step_one_has_no_activities_or_analysis(self, context_service):
        """Step 1 should not have activities or analysis summary."""
        session_id = uuid4()
        context = await context_service.build_context(
            session_id=session_id,
            current_step=1,
            user_message="Test message"
        )
        assert "activities" not in context
        assert "analysis_summary" not in context


class TestUnknownStepHandling:
    """Tests for unknown step name handling."""

    @pytest.mark.asyncio
    async def test_invalid_step_name_handling(self, context_service):
        """Invalid step should raise ValueError, not return 'Unknown'."""
        session_id = uuid4()
        # Now that we validate, step 99 should raise ValueError
        with pytest.raises(ValueError, match="current_step must be between 1 and 5"):
            await context_service.build_context(
                session_id=session_id,
                current_step=99,
                user_message="Test message"
            )
