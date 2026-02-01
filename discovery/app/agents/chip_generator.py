"""Quick action chip generator for conversational UI."""
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Union

if TYPE_CHECKING:
    from app.agents.message_formatter import QuickAction

logger = logging.getLogger(__name__)


@dataclass
class Chip:
    """Represents a clickable choice chip for user interaction.

    Attributes:
        label: Display text for the chip.
        value: Value sent to API when chip is selected.
        type: Chip type, typically "choice".
        style: Visual style, "primary" for recommended or "secondary".
        disabled: Whether the chip is disabled/unclickable.
        icon: Optional icon identifier for the chip.

    Note:
        The field ordering (required fields first, optional `icon` last) is
        intentional and valid in Python 3.10+ where fields with defaults can
        follow fields without defaults in dataclasses.
    """

    label: str
    value: str
    type: str
    style: str
    disabled: bool
    icon: Optional[str] = None

    def to_quick_action(self) -> "QuickAction":
        """Convert this Chip to a QuickAction for message formatting.

        Returns:
            A QuickAction with the chip's label and value.
        """
        from app.agents.message_formatter import QuickAction

        return QuickAction(label=self.label, value=self.value)


class QuickActionChipGenerator:
    """Generator for quick action chips in conversational interfaces.

    Provides methods to create clickable choice chips for various
    contexts including general choices, column selection, confirmations,
    and O*NET occupation suggestions.
    """

    def generate(
        self,
        choices: list[Union[str, dict]],
        max_chips: Optional[int] = None,
        primary_index: Optional[int] = None,
    ) -> list[Chip]:
        """Generate chips from a list of choices.

        Args:
            choices: List of choices. Can be strings or dicts with
                label, icon, and disabled fields.
            max_chips: Maximum number of chips to generate. If None,
                all choices are included.
            primary_index: Index of the chip to mark as primary style.
                If None or out of range, all chips use secondary style.

        Returns:
            List of Chip objects.
        """
        if not choices:
            return []

        # Limit to max_chips if specified
        limited_choices = choices[:max_chips] if max_chips else choices

        chips = []
        for i, choice in enumerate(limited_choices):
            chip = self._create_chip_from_choice(choice)

            # Apply primary style if this is the primary index
            if primary_index is not None and i == primary_index:
                chip.style = "primary"

            chips.append(chip)

        return chips

    def _create_chip_from_choice(
        self,
        choice: Union[str, dict],
    ) -> Chip:
        """Create a Chip from a string or dict choice.

        Args:
            choice: A string choice or dict with label, icon, disabled.

        Returns:
            A Chip object with extracted/default values.
        """
        if isinstance(choice, dict):
            label = choice.get("label", "")
            icon = choice.get("icon")
            disabled = choice.get("disabled", False)

            if not label:
                logger.warning(
                    "Dict choice has empty or missing label: %r",
                    choice,
                )
        else:
            label = str(choice)
            icon = None
            disabled = False

        return Chip(
            label=label,
            value=label,
            type="choice",
            icon=icon,
            style="secondary",
            disabled=disabled,
        )

    def generate_column_chips(
        self,
        columns: list[str],
    ) -> list[Chip]:
        """Generate chips for column selection in data upload flows.

        Args:
            columns: List of column names to create chips for.

        Returns:
            List of Chip objects for column selection.
        """
        return self.generate(choices=columns)

    def generate_confirmation_chips(self) -> list[Chip]:
        """Generate Yes/No confirmation chips.

        Returns:
            List containing Yes and No chips with appropriate icons.
        """
        return self.generate(
            choices=[
                {"label": "Yes", "icon": "check"},
                {"label": "No", "icon": "x"},
            ],
        )

    def generate_onet_chips(
        self,
        suggestions: list[dict],
    ) -> list[Chip]:
        """Generate chips for O*NET occupation suggestions.

        Args:
            suggestions: List of O*NET suggestion dicts with code,
                title, and score fields.

        Returns:
            List of Chip objects with occupation titles as labels
            and O*NET codes as values. Suggestions missing required
            fields (code or title) are skipped with a warning.
        """
        if not suggestions:
            return []

        chips = []
        for suggestion in suggestions:
            code = suggestion.get("code", "")
            title = suggestion.get("title", "")

            # Skip suggestions missing required fields
            if not code or not title:
                logger.warning(
                    "Skipping O*NET suggestion with missing required fields: "
                    "code=%r, title=%r",
                    code,
                    title,
                )
                continue

            chips.append(
                Chip(
                    label=title,
                    value=code,
                    type="choice",
                    style="secondary",
                    disabled=False,
                )
            )

        return chips
