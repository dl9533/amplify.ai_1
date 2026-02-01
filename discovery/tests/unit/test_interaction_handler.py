# discovery/tests/unit/test_interaction_handler.py
"""Unit tests for the BrainstormingHandler interaction handler."""
import pytest

from app.agents.interaction_handler import BrainstormingHandler


@pytest.fixture
def handler():
    """Create a fresh BrainstormingHandler for each test."""
    return BrainstormingHandler()


class TestQuestionFormatting:
    """Tests for question formatting."""

    def test_format_single_question(self, handler):
        """Should format a single question with choices."""
        result = handler.format_question(
            question="Which column contains the role?",
            choices=["Column A", "Column B", "Column C"],
        )

        assert result.question == "Which column contains the role?"
        assert len(result.choices) == 3
        assert result.allow_freeform is False

    def test_format_question_with_freeform_option(self, handler):
        """Should allow freeform input when specified."""
        result = handler.format_question(
            question="What is the role name?",
            choices=["Engineer", "Analyst"],
            allow_freeform=True,
        )

        assert result.allow_freeform is True

    def test_limit_choices_to_five(self, handler):
        """Should limit choices to max 5 options."""
        result = handler.format_question(
            question="Pick one",
            choices=["A", "B", "C", "D", "E", "F", "G"],
        )

        assert len(result.choices) <= 5

    def test_format_question_preserves_choices_order(self, handler):
        """Should preserve the order of choices."""
        result = handler.format_question(
            question="Order matters?",
            choices=["First", "Second", "Third"],
        )

        assert result.choices == ["First", "Second", "Third"]

    def test_format_question_empty_choices(self, handler):
        """Should handle empty choices list."""
        result = handler.format_question(
            question="No choices?",
            choices=[],
        )

        assert result.choices == []
        assert result.question == "No choices?"


class TestOneQuestionAtATime:
    """Tests for one-question-at-a-time pattern."""

    def test_queue_multiple_questions(self, handler):
        """Should queue multiple questions."""
        handler.queue_question("Question 1?", ["A", "B"])
        handler.queue_question("Question 2?", ["C", "D"])

        assert handler.pending_count == 2

    def test_get_next_returns_first_queued(self, handler):
        """Should return questions in FIFO order."""
        handler.queue_question("First?", ["A"])
        handler.queue_question("Second?", ["B"])

        result = handler.get_next_question()

        assert result.question == "First?"

    def test_mark_answered_removes_from_queue(self, handler):
        """Should remove answered question from queue."""
        handler.queue_question("Question?", ["A", "B"])

        handler.get_next_question()
        handler.mark_answered("A")

        assert handler.pending_count == 0

    def test_get_next_returns_none_when_empty(self, handler):
        """Should return None when no questions are queued."""
        result = handler.get_next_question()

        assert result is None

    def test_pending_count_initially_zero(self, handler):
        """Should have zero pending count initially."""
        assert handler.pending_count == 0

    def test_fifo_order_after_answering(self, handler):
        """Should maintain FIFO order after answering questions."""
        handler.queue_question("First?", ["A"])
        handler.queue_question("Second?", ["B"])
        handler.queue_question("Third?", ["C"])

        handler.get_next_question()
        handler.mark_answered("A")

        next_question = handler.get_next_question()
        assert next_question.question == "Second?"

    def test_queue_question_with_freeform(self, handler):
        """Should queue question with freeform option."""
        handler.queue_question("What else?", ["Option 1"], allow_freeform=True)

        result = handler.get_next_question()
        assert result.allow_freeform is True


class TestResponseParsing:
    """Tests for parsing user responses."""

    def test_match_choice_by_text(self, handler):
        """Should match user response to choice."""
        handler._current_choices = ["Column A", "Column B"]

        result = handler.parse_response("Column A")

        assert result.matched_choice == "Column A"
        assert result.is_freeform is False

    def test_detect_freeform_response(self, handler):
        """Should detect freeform response when no match."""
        handler._current_choices = ["Option 1", "Option 2"]
        handler._allow_freeform = True

        result = handler.parse_response("Something else entirely")

        assert result.is_freeform is True
        assert result.freeform_value == "Something else entirely"

    def test_case_insensitive_matching(self, handler):
        """Should match choices case-insensitively."""
        handler._current_choices = ["Column A", "Column B"]

        result = handler.parse_response("column a")

        assert result.matched_choice == "Column A"
        assert result.is_freeform is False

    def test_no_match_freeform_disabled(self, handler):
        """Should return no match when freeform is disabled."""
        handler._current_choices = ["Option 1", "Option 2"]
        handler._allow_freeform = False

        result = handler.parse_response("Something else")

        assert result.matched_choice is None
        assert result.is_freeform is False
        assert result.freeform_value is None

    def test_partial_match_not_accepted(self, handler):
        """Should not accept partial matches."""
        handler._current_choices = ["Column A", "Column B"]

        result = handler.parse_response("Column")

        # Should not match - partial match is not exact
        assert result.matched_choice is None

    def test_whitespace_trimmed_in_matching(self, handler):
        """Should trim whitespace when matching."""
        handler._current_choices = ["Column A", "Column B"]

        result = handler.parse_response("  Column A  ")

        assert result.matched_choice == "Column A"

    def test_parse_response_with_empty_choices(self, handler):
        """Should handle parsing when no choices exist."""
        handler._current_choices = []
        handler._allow_freeform = True

        result = handler.parse_response("Any response")

        assert result.is_freeform is True
        assert result.freeform_value == "Any response"
