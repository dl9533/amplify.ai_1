# discovery/app/agents/interaction_handler.py
"""Brainstorming interaction handler for one-question-at-a-time user interactions."""
from collections import deque
from dataclasses import dataclass
from typing import Optional


@dataclass
class FormattedQuestion:
    """A formatted question with choices for user interaction.

    Attributes:
        question: The question text to present to the user.
        choices: List of choices the user can select from.
        allow_freeform: Whether freeform text input is allowed.
    """

    question: str
    choices: list[str]
    allow_freeform: bool = False


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

    Attributes:
        MAX_CHOICES: Maximum number of choices allowed per question (5).
    """

    MAX_CHOICES: int = 5

    def __init__(self) -> None:
        """Initialize the BrainstormingHandler with an empty question queue."""
        self._queue: deque[FormattedQuestion] = deque()
        self._current_choices: list[str] = []
        self._allow_freeform: bool = False

    def format_question(
        self,
        question: str,
        choices: list[str],
        allow_freeform: bool = False,
    ) -> FormattedQuestion:
        """Format a question with choices for user interaction.

        Args:
            question: The question text to present.
            choices: List of choices for the user to select from.
            allow_freeform: Whether to allow freeform text input. Defaults to False.

        Returns:
            A FormattedQuestion with the question, limited choices, and freeform setting.
        """
        # Limit choices to MAX_CHOICES
        limited_choices = choices[: self.MAX_CHOICES]

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
        This also sets the internal state for response parsing.

        Returns:
            The next FormattedQuestion, or None if the queue is empty.
        """
        if not self._queue:
            return None

        question = self._queue[0]
        # Set internal state for response parsing
        self._current_choices = question.choices
        self._allow_freeform = question.allow_freeform

        return question

    def mark_answered(self, answer: str) -> None:
        """Mark the current question as answered and remove it from the queue.

        Args:
            answer: The user's answer (used for logging/tracking purposes).
        """
        if self._queue:
            self._queue.popleft()
            # Reset internal state
            self._current_choices = []
            self._allow_freeform = False

    def parse_response(self, response: str) -> ParsedResponse:
        """Parse a user response and match it against available choices.

        Matching is case-insensitive and whitespace is trimmed.
        If no match is found and freeform is allowed, the response is
        returned as a freeform value.

        Args:
            response: The user's response text.

        Returns:
            A ParsedResponse with match information.
        """
        # Trim whitespace
        cleaned_response = response.strip()
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
