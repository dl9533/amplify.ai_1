"""Chat message formatter for agent responses."""
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Union

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


@dataclass
class QuickAction:
    """Represents a quick action button/chip for user interaction.

    Attributes:
        label: Display text for the quick action.
        value: Value sent to API when action is selected.
    """

    label: str
    value: str


@dataclass
class FormattedMessage:
    """A formatted chat message for display.

    Attributes:
        role: Message role ("user" or "assistant").
        content: The message content text.
        timestamp: When the message was created.
        agent_type: Type of agent (for assistant messages).
        quick_actions: Optional list of quick action choices.
    """

    role: str
    content: str
    timestamp: datetime
    agent_type: Optional[str] = None
    quick_actions: list[QuickAction] = field(default_factory=list)


@dataclass
class ConversationTurn:
    """A conversation turn consisting of user input and agent response.

    Attributes:
        user_message: The user's message in this turn.
        agent_message: The agent's response in this turn.
    """

    user_message: FormattedMessage
    agent_message: FormattedMessage


class ChatMessageFormatter:
    """Formatter for chat messages between users and agents.

    Provides methods to format agent and user messages with consistent
    structure, including timestamps, quick actions, and conversation
    history grouping.
    """

    def format_agent_message(
        self,
        content: str,
        agent_type: str,
    ) -> FormattedMessage:
        """Format an agent message with metadata.

        Args:
            content: The message content. Empty strings are allowed for UI
                purposes (e.g., placeholder messages, typing indicators).
            agent_type: The type of agent sending the message.

        Returns:
            A FormattedMessage with role="assistant" and metadata.
        """
        return FormattedMessage(
            role="assistant",
            content=content,
            timestamp=_utc_now(),
            agent_type=agent_type,
        )

    def format_user_message(
        self,
        content: str,
    ) -> FormattedMessage:
        """Format a user message.

        Args:
            content: The message content. Empty strings are allowed for UI
                purposes (e.g., placeholder messages).

        Returns:
            A FormattedMessage with role="user".
        """
        return FormattedMessage(
            role="user",
            content=content,
            timestamp=_utc_now(),
        )

    def format_with_quick_actions(
        self,
        content: str,
        choices: list[Union[str, tuple[str, str]]],
        agent_type: str = "assistant",
    ) -> FormattedMessage:
        """Format a message with quick action choices.

        Args:
            content: The message content. Empty strings are allowed for UI
                purposes (e.g., when only quick actions are displayed).
            choices: List of choices. Can be simple strings or (label, value)
                tuples. Malformed tuples (not exactly 2 elements) are skipped
                with a warning logged.
            agent_type: The type of agent sending the message.

        Returns:
            A FormattedMessage with quick_actions populated.
        """
        quick_actions = []
        for choice in choices:
            if isinstance(choice, tuple):
                if len(choice) != 2:
                    logger.warning(
                        "Skipping malformed choice tuple with %d elements: %r",
                        len(choice),
                        choice,
                    )
                    continue
                label, value = choice
                quick_actions.append(QuickAction(label=label, value=value))
            else:
                # Simple string: use as both label and value
                quick_actions.append(QuickAction(label=choice, value=choice))

        return FormattedMessage(
            role="assistant",
            content=content,
            timestamp=_utc_now(),
            agent_type=agent_type,
            quick_actions=quick_actions,
        )

    def format_history(
        self,
        messages: list[dict],
    ) -> list[FormattedMessage]:
        """Format message history for UI display.

        Args:
            messages: List of message dictionaries with role, content,
                     and optional agent_type.

        Returns:
            List of FormattedMessage objects.
        """
        formatted = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            agent_type = msg.get("agent_type")
            timestamp = msg.get("timestamp")

            # Use provided timestamp or current time
            if timestamp is None:
                timestamp = _utc_now()
            elif isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp)
                except ValueError:
                    logger.warning(
                        "Invalid ISO timestamp '%s', using current time",
                        timestamp,
                    )
                    timestamp = _utc_now()

            formatted.append(
                FormattedMessage(
                    role=role,
                    content=content,
                    timestamp=timestamp,
                    agent_type=agent_type,
                )
            )

        return formatted

    def group_by_turn(
        self,
        messages: list[dict],
    ) -> list[ConversationTurn]:
        """Group messages by conversation turn (user + agent pairs).

        This method expects strict alternation between user and assistant
        messages. Incomplete turns (e.g., a user message without a following
        assistant response) at the end of the conversation are discarded.

        Note:
            - Consecutive same-role messages will result in the first message
              being paired with the subsequent different-role message, and the
              extra same-role message being discarded or orphaned.
            - If the conversation ends with a user message (no assistant
              response yet), that message will not appear in the returned turns.

        Args:
            messages: List of message dictionaries.

        Returns:
            List of ConversationTurn objects, each containing a user
            message and corresponding agent response.
        """
        turns = []
        formatted = self.format_history(messages)

        i = 0
        while i < len(formatted):
            user_msg = None
            agent_msg = None

            # Find user message
            if i < len(formatted) and formatted[i].role == "user":
                user_msg = formatted[i]
                i += 1

            # Find agent message
            if i < len(formatted) and formatted[i].role == "assistant":
                agent_msg = formatted[i]
                i += 1

            # Create turn if we have both messages
            if user_msg is not None and agent_msg is not None:
                turns.append(
                    ConversationTurn(
                        user_message=user_msg,
                        agent_message=agent_msg,
                    )
                )
            elif user_msg is not None or agent_msg is not None:
                # Handle incomplete turns by continuing to next iteration
                # This could happen at the end of a conversation
                continue

        return turns
