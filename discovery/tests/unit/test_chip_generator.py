# discovery/tests/unit/test_chip_generator.py
"""Tests for QuickActionChipGenerator."""
import pytest

from app.agents.chip_generator import QuickActionChipGenerator, Chip


@pytest.fixture
def generator():
    """Create a QuickActionChipGenerator instance."""
    return QuickActionChipGenerator()


class TestChipGeneration:
    """Tests for quick action chip generation."""

    def test_generate_choice_chips(self, generator):
        """Should generate chips from choices."""
        result = generator.generate(
            choices=["Option A", "Option B", "Option C"],
        )

        assert len(result) == 3
        assert all(chip.type == "choice" for chip in result)

    def test_generate_with_icons(self, generator):
        """Should include icons when specified."""
        result = generator.generate(
            choices=[
                {"label": "Yes", "icon": "check"},
                {"label": "No", "icon": "x"},
            ],
        )

        assert result[0].icon == "check"
        assert result[1].icon == "x"

    def test_limit_to_max_chips(self, generator):
        """Should limit to maximum number of chips."""
        result = generator.generate(
            choices=["A", "B", "C", "D", "E", "F", "G", "H"],
            max_chips=5,
        )

        assert len(result) == 5

    def test_string_choice_uses_label_as_value(self, generator):
        """Should use label as value for string choices."""
        result = generator.generate(choices=["Test Option"])

        assert result[0].label == "Test Option"
        assert result[0].value == "Test Option"

    def test_dict_choice_extracts_fields(self, generator):
        """Should extract label, icon, disabled from dict choices."""
        result = generator.generate(
            choices=[
                {"label": "Custom Label", "icon": "star", "disabled": True},
            ],
        )

        assert result[0].label == "Custom Label"
        assert result[0].value == "Custom Label"
        assert result[0].icon == "star"
        assert result[0].disabled is True

    def test_default_style_is_secondary(self, generator):
        """Should default to secondary style."""
        result = generator.generate(choices=["Option"])

        assert result[0].style == "secondary"

    def test_empty_choices_returns_empty_list(self, generator):
        """Should return empty list for empty choices."""
        result = generator.generate(choices=[])

        assert result == []


class TestContextualChips:
    """Tests for context-aware chip generation."""

    def test_generate_column_selection_chips(self, generator):
        """Should generate chips for column selection."""
        result = generator.generate_column_chips(
            columns=["Name", "Department", "Title"],
        )

        assert len(result) == 3
        assert any("Title" in chip.label for chip in result)

    def test_generate_column_chips_type_is_choice(self, generator):
        """Should set type to choice for column chips."""
        result = generator.generate_column_chips(
            columns=["Name", "Email"],
        )

        assert all(chip.type == "choice" for chip in result)

    def test_generate_confirmation_chips(self, generator):
        """Should generate yes/no confirmation chips."""
        result = generator.generate_confirmation_chips()

        assert len(result) == 2
        assert any(chip.label == "Yes" for chip in result)
        assert any(chip.label == "No" for chip in result)

    def test_confirmation_chips_have_icons(self, generator):
        """Should include icons for confirmation chips."""
        result = generator.generate_confirmation_chips()

        yes_chip = next(c for c in result if c.label == "Yes")
        no_chip = next(c for c in result if c.label == "No")

        assert yes_chip.icon == "check"
        assert no_chip.icon == "x"

    def test_generate_onet_suggestion_chips(self, generator):
        """Should generate chips for O*NET suggestions."""
        suggestions = [
            {"code": "15-1252.00", "title": "Software Developers", "score": 0.95},
            {"code": "15-1254.00", "title": "Web Developers", "score": 0.85},
        ]

        result = generator.generate_onet_chips(suggestions)

        assert len(result) == 2
        assert "Software Developers" in result[0].label

    def test_onet_chips_include_code_in_value(self, generator):
        """Should include O*NET code in chip value."""
        suggestions = [
            {"code": "15-1252.00", "title": "Software Developers", "score": 0.95},
        ]

        result = generator.generate_onet_chips(suggestions)

        assert result[0].value == "15-1252.00"

    def test_onet_chips_empty_suggestions(self, generator):
        """Should return empty list for empty suggestions."""
        result = generator.generate_onet_chips([])

        assert result == []


class TestChipStyling:
    """Tests for chip styling."""

    def test_primary_chip_style(self, generator):
        """Should apply primary style to recommended option."""
        result = generator.generate(
            choices=["Recommended", "Alternative"],
            primary_index=0,
        )

        assert result[0].style == "primary"
        assert result[1].style == "secondary"

    def test_primary_index_middle(self, generator):
        """Should apply primary style to middle option."""
        result = generator.generate(
            choices=["A", "B", "C"],
            primary_index=1,
        )

        assert result[0].style == "secondary"
        assert result[1].style == "primary"
        assert result[2].style == "secondary"

    def test_disabled_chip_state(self, generator):
        """Should support disabled chips."""
        result = generator.generate(
            choices=[
                {"label": "Available", "disabled": False},
                {"label": "Unavailable", "disabled": True},
            ],
        )

        assert result[0].disabled is False
        assert result[1].disabled is True

    def test_default_disabled_is_false(self, generator):
        """Should default disabled to False."""
        result = generator.generate(choices=["Option"])

        assert result[0].disabled is False

    def test_primary_index_out_of_range_ignored(self, generator):
        """Should ignore primary_index if out of range."""
        result = generator.generate(
            choices=["A", "B"],
            primary_index=10,
        )

        assert all(chip.style == "secondary" for chip in result)


class TestChipDataclass:
    """Tests for Chip dataclass."""

    def test_chip_creation(self):
        """Should create Chip with all fields."""
        chip = Chip(
            label="Test",
            value="test_value",
            type="choice",
            icon="star",
            style="primary",
            disabled=True,
        )

        assert chip.label == "Test"
        assert chip.value == "test_value"
        assert chip.type == "choice"
        assert chip.icon == "star"
        assert chip.style == "primary"
        assert chip.disabled is True

    def test_chip_optional_icon(self):
        """Should allow None for optional icon."""
        chip = Chip(
            label="Test",
            value="test",
            type="choice",
            style="secondary",
            disabled=False,
        )

        assert chip.icon is None

    def test_chip_to_quick_action(self):
        """Should convert Chip to QuickAction."""
        chip = Chip(
            label="Test Label",
            value="test_value",
            type="choice",
            style="primary",
            disabled=False,
            icon="star",
        )

        quick_action = chip.to_quick_action()

        assert quick_action.label == "Test Label"
        assert quick_action.value == "test_value"


class TestEdgeCases:
    """Tests for edge cases and validation."""

    def test_generate_with_empty_choices_list(self, generator):
        """Should return empty list when choices is empty."""
        result = generator.generate(choices=[])

        assert result == []

    def test_generate_onet_chips_with_empty_suggestions(self, generator):
        """Should return empty list when suggestions is empty."""
        result = generator.generate_onet_chips([])

        assert result == []

    def test_generate_onet_chips_skips_missing_code(self, generator):
        """Should skip suggestions missing code field."""
        suggestions = [
            {"title": "Software Developer", "score": 0.95},  # missing code
            {"code": "15-1254.00", "title": "Web Developer", "score": 0.85},
        ]

        result = generator.generate_onet_chips(suggestions)

        assert len(result) == 1
        assert result[0].label == "Web Developer"

    def test_generate_onet_chips_skips_missing_title(self, generator):
        """Should skip suggestions missing title field."""
        suggestions = [
            {"code": "15-1252.00", "score": 0.95},  # missing title
            {"code": "15-1254.00", "title": "Web Developer", "score": 0.85},
        ]

        result = generator.generate_onet_chips(suggestions)

        assert len(result) == 1
        assert result[0].value == "15-1254.00"

    def test_generate_onet_chips_skips_empty_code(self, generator):
        """Should skip suggestions with empty code."""
        suggestions = [
            {"code": "", "title": "Software Developer", "score": 0.95},
            {"code": "15-1254.00", "title": "Web Developer", "score": 0.85},
        ]

        result = generator.generate_onet_chips(suggestions)

        assert len(result) == 1
        assert result[0].label == "Web Developer"

    def test_generate_onet_chips_skips_empty_title(self, generator):
        """Should skip suggestions with empty title."""
        suggestions = [
            {"code": "15-1252.00", "title": "", "score": 0.95},
            {"code": "15-1254.00", "title": "Web Developer", "score": 0.85},
        ]

        result = generator.generate_onet_chips(suggestions)

        assert len(result) == 1
        assert result[0].value == "15-1254.00"

    def test_dict_choice_with_empty_label_creates_chip(self, generator):
        """Should create chip even with empty label (logs warning)."""
        result = generator.generate(
            choices=[{"label": "", "icon": "warning"}],
        )

        assert len(result) == 1
        assert result[0].label == ""
        assert result[0].icon == "warning"

    def test_dict_choice_missing_label_creates_chip(self, generator):
        """Should create chip with empty label when label key missing."""
        result = generator.generate(
            choices=[{"icon": "info"}],
        )

        assert len(result) == 1
        assert result[0].label == ""

    def test_generate_column_chips_with_empty_columns(self, generator):
        """Should return empty list for empty columns."""
        result = generator.generate_column_chips(columns=[])

        assert result == []
