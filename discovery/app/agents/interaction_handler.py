# discovery/app/agents/interaction_handler.py
"""Brainstorming interaction handler for one-question-at-a-time user interactions."""
from collections import deque
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FormattedQuestion:
    """A formatted question with choices for user interaction.

    Attributes:
        question: The question text to present to the user.
        choices: List of choices the user can select from.
        allow_freeform: Whether freeform text input is allowed.
        answer: The user's answer after the question is answered (for tracking).
    """

    question: str
    choices: list[str]
    allow_freeform: bool = False
    answer: Optional[str] = field(default=None)


@dataclass
class ParsedResponse:
    """A parsed user response with match information.

    Attributes:
        matched_choice: The choice that matched the user's response (if any).
        is_freeform: Whether the response is a freeform text input.
        freeform_value: The freeform text value (if freeform).
    """

    matched_choice: Optional[str] = None
    is_freeform: bool = False
    freeform_value: Optional[str] = None


class BrainstormingHandler:
    """Handler for one-question-at-a-time brainstorming interactions.

    This handler manages a queue of questions to present to users one at a time,
    formats questions with choices, and parses user responses to match against
    available choices or detect freeform input.

    Usage Pattern:
        1. queue_question() - Add questions to the queue
        2. get_next_question() - Retrieve the next question to display
        3. parse_response() - Parse the user's response
        4. mark_answered() - Mark question as answered and move to next
        5. Repeat steps 2-4 until queue is empty

    Example:
        handler = BrainstormingHandler()
        handler.queue_question("Which column?", ["A", "B", "C"])
        question = handler.get_next_question()
        # Display question to user...
        response = handler.parse_response(user_input)
        handler.mark_answered(user_input)

    Attributes:
        MAX_CHOICES: Maximum number of choices allowed per question (5).
            Choices beyond this limit are silently truncated.
        last_answered_question: The most recently answered FormattedQuestion
            (with the answer stored), or None if no questions have been answered.
    """

    MAX_CHOICES: int = 5

    def __init__(self) -> None:
        """Initialize the BrainstormingHandler with an empty question queue."""
        self._queue: deque[FormattedQuestion] = deque()
        self._current_choices: list[str] = []
        self._allow_freeform: bool = False
        self._question_active: bool = False
        self.last_answered_question: Optional[FormattedQuestion] = None

    def format_question(
        self,
        question: str,
        choices: list[str],
        allow_freeform: bool = False,
    ) -> FormattedQuestion:
        """Format a question with choices for user interaction.

        Args:
            question: The question text to present. May be empty for UI-only prompts.
            choices: List of choices for the user to select from.
                Empty strings are filtered out. Choices beyond MAX_CHOICES (5)
                are silently truncated.
            allow_freeform: Whether to allow freeform text input. Defaults to False.

        Returns:
            A FormattedQuestion with the question, filtered/limited choices,
            and freeform setting.
        """
        # Filter out empty strings from choices
        filtered_choices = [c for c in choices if c]
        # Limit choices to MAX_CHOICES
        limited_choices = filtered_choices[: self.MAX_CHOICES]

        return FormattedQuestion(
            question=question,
            choices=limited_choices,
            allow_freeform=allow_freeform,
        )

    def queue_question(
        self,
        question: str,
        choices: list[str],
        allow_freeform: bool = False,
    ) -> None:
        """Queue a question for later retrieval.

        Questions are queued in FIFO order and can be retrieved one at a time
        using get_next_question().

        Args:
            question: The question text to queue.
            choices: List of choices for the user to select from.
            allow_freeform: Whether to allow freeform text input. Defaults to False.
        """
        formatted = self.format_question(question, choices, allow_freeform)
        self._queue.append(formatted)

    @property
    def pending_count(self) -> int:
        """Return the number of pending questions in the queue.

        Returns:
            The count of questions waiting to be answered.
        """
        return len(self._queue)

    def get_next_question(self) -> Optional[FormattedQuestion]:
        """Get the next question from the queue without removing it.

        The question remains in the queue until mark_answered() is called.
        This also sets the internal state for response parsing on the first call.
        Subsequent calls before mark_answered() preserve the original state to
        prevent race conditions.

        Returns:
            The next FormattedQuestion, or None if the queue is empty.
        """
        if not self._queue:
            return None

        question = self._queue[0]
        # Only set internal state on the first call to prevent race conditions
        if not self._question_active:
            self._current_choices = question.choices
            self._allow_freeform = question.allow_freeform
            self._question_active = True

        return question

    def mark_answered(self, answer: str) -> None:
        """Mark the current question as answered and remove it from the queue.

        The answered question is stored in last_answered_question with the
        answer recorded for potential tracking or audit purposes.

        Args:
            answer: The user's answer to be stored in the answered question.
        """
        if self._queue:
            answered_question = self._queue.popleft()
            # Store the answer in the question for tracking
            answered_question.answer = answer
            self.last_answered_question = answered_question
            # Reset internal state
            self._current_choices = []
            self._allow_freeform = False
            self._question_active = False

    def parse_response(self, response: str) -> ParsedResponse:
        """Parse a user response and match it against available choices.

        Matching is case-insensitive and whitespace is trimmed.
        If no match is found and freeform is allowed, the response is
        returned as a freeform value.

        Note:
            If called before get_next_question(), the internal state will have
            no choices set, resulting in a "no match" response (matched_choice=None,
            is_freeform=False). This is intentional behavior - always call
            get_next_question() first to set up the parsing context.

        Args:
            response: The user's response text.

        Returns:
            A ParsedResponse with match information. Empty or whitespace-only
            responses return a "no match" response (not freeform).
        """
        # Trim whitespace
        cleaned_response = response.strip()

        # Empty responses are treated as no match (not freeform)
        if not cleaned_response:
            return ParsedResponse(
                matched_choice=None,
                is_freeform=False,
                freeform_value=None,
            )

        response_lower = cleaned_response.lower()

        # Try to match against choices (case-insensitive)
        for choice in self._current_choices:
            if choice.lower() == response_lower:
                return ParsedResponse(
                    matched_choice=choice,
                    is_freeform=False,
                    freeform_value=None,
                )

        # No match found - check if freeform is allowed
        if self._allow_freeform:
            return ParsedResponse(
                matched_choice=None,
                is_freeform=True,
                freeform_value=cleaned_response,
            )

        # No match and freeform not allowed
        return ParsedResponse(
            matched_choice=None,
            is_freeform=False,
            freeform_value=None,
        )
