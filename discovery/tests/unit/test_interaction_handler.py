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

    def test_format_question_filters_empty_choices(self, handler):
        """Should filter out empty strings from choices."""
        result = handler.format_question(
            question="Filter empties?",
            choices=["Valid", "", "Also Valid", "", "Third"],
        )

        # Empty strings should be filtered out
        assert "" not in result.choices
        assert len(result.choices) == 3  # "Valid", "Also Valid", "Third"
        assert result.choices == ["Valid", "Also Valid", "Third"]


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

    def test_get_next_question_twice_preserves_first_state(self, handler):
        """Should preserve state when get_next_question is called multiple times."""
        # Queue a question with freeform enabled
        handler.queue_question("First?", ["A", "B"], allow_freeform=True)

        # Get the question the first time - this sets the state
        first_call = handler.get_next_question()
        assert first_call.question == "First?"

        # Manually change the question's attributes (simulating a race condition)
        handler._queue[0] = handler.format_question(
            "Modified?", ["X", "Y", "Z"], allow_freeform=False
        )

        # Get the question again - state should NOT be overwritten
        second_call = handler.get_next_question()

        # The returned question is the modified one from the queue
        assert second_call.question == "Modified?"

        # But the internal state should still be from the first call
        assert handler._current_choices == ["A", "B"]
        assert handler._allow_freeform is True

    def test_mark_answered_stores_answer(self, handler):
        """Should store the answer in the answered question."""
        handler.queue_question("What is your choice?", ["A", "B"])
        handler.get_next_question()

        handler.mark_answered("A")

        # The answer should be stored in last_answered_question
        assert handler.last_answered_question is not None
        assert handler.last_answered_question.question == "What is your choice?"
        assert handler.last_answered_question.answer == "A"

    def test_mark_answered_resets_question_active_flag(self, handler):
        """Should reset the question active flag after marking answered."""
        handler.queue_question("First?", ["A"])
        handler.queue_question("Second?", ["X", "Y"])

        # Get first question and answer it
        handler.get_next_question()
        assert handler._question_active is True
        handler.mark_answered("A")
        assert handler._question_active is False

        # Get second question - should set new state
        handler.get_next_question()
        assert handler._current_choices == ["X", "Y"]


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

    def test_parse_response_with_empty_string(self, handler):
        """Should return no match for empty or whitespace-only responses."""
        handler._current_choices = ["Option 1", "Option 2"]
        handler._allow_freeform = True

        # Test empty string
        result_empty = handler.parse_response("")
        assert result_empty.matched_choice is None
        assert result_empty.is_freeform is False
        assert result_empty.freeform_value is None

        # Test whitespace-only string
        result_whitespace = handler.parse_response("   ")
        assert result_whitespace.matched_choice is None
        assert result_whitespace.is_freeform is False
        assert result_whitespace.freeform_value is None

    def test_parse_response_empty_not_treated_as_freeform(self, handler):
        """Empty responses should not be treated as freeform even when freeform is allowed."""
        handler._current_choices = []
        handler._allow_freeform = True

        result = handler.parse_response("")

        # Even with freeform enabled, empty should not be freeform
        assert result.is_freeform is False
        assert result.freeform_value is None
