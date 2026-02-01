"""Upload Subagent for handling file uploads and column detection."""
import csv
import io
from typing import Any, Optional

from app.agents.base import BaseSubagent


class UploadSubagent(BaseSubagent):
    """Subagent for handling file uploads, column detection, and mapping suggestions.

    This agent processes uploaded files (CSV/XLSX), detects column names,
    and suggests mappings to required fields using a brainstorming-style
    interaction with one question at a time.

    Attributes:
        agent_type: The type identifier for this agent ('upload').
        _file_uploaded: Whether a file has been uploaded.
        _columns: List of detected column names.
        _pending_question: The current question awaiting user response.
        _column_mappings: Dictionary of confirmed column mappings.
    """

    agent_type: str = "upload"

    # Supported file types for upload
    SUPPORTED_FILE_TYPES: set[str] = {"csv"}  # Add "xlsx" when implemented

    # Column mapping keywords for suggestions
    _ROLE_KEYWORDS = ["role", "title", "job", "position"]
    _DEPARTMENT_KEYWORDS = ["department", "dept", "division", "team", "unit"]
    _HEADCOUNT_KEYWORDS = ["headcount", "count", "fte", "employees", "staff", "size"]

    # Order in which column mappings are requested
    _MAPPING_ORDER = ["role_column", "department_column", "headcount_column"]

    def __init__(self, session: Any, memory_service: Any) -> None:
        """Initialize the UploadSubagent.

        Args:
            session: Database session for persistence operations.
            memory_service: Service for agent memory management.
        """
        super().__init__(session, memory_service)
        self._file_uploaded: bool = False
        self._columns: list[str] = []
        self._pending_question: Optional[str] = None
        self._column_mappings: dict[str, str] = {}

    async def detect_columns(self, file_content: str, file_type: str = "csv") -> list[str]:
        """Detect column names from uploaded file content.

        Args:
            file_content: The raw content of the uploaded file.
            file_type: The type of file ('csv' or 'xlsx').

        Returns:
            A list of column names detected from the file.

        Raises:
            ValueError: If the file type is not supported.
        """
        if file_type not in self.SUPPORTED_FILE_TYPES:
            raise ValueError(
                f"Unsupported file type: {file_type}. Supported: {self.SUPPORTED_FILE_TYPES}"
            )
        if file_type == "csv":
            return self._parse_csv_columns(file_content)
        return []

    def _parse_csv_columns(self, file_content: str) -> list[str]:
        """Parse column names from CSV content.

        Args:
            file_content: The raw CSV content.

        Returns:
            A list of column names from the first row.
        """
        reader = csv.reader(io.StringIO(file_content))
        try:
            headers = next(reader)
            return [h.strip() for h in headers]
        except StopIteration:
            return []

    async def suggest_column_mappings(self, columns: list[str]) -> dict[str, Optional[str]]:
        """Suggest which columns map to required fields.

        Analyzes column names and suggests mappings for:
        - role_column: Column containing role/job title information
        - department_column: Column containing department information
        - headcount_column: Column containing headcount/FTE information

        Args:
            columns: List of column names from the uploaded file.

        Returns:
            A dictionary with suggested column mappings.
        """
        suggestions: dict[str, Optional[str]] = {
            "role_column": None,
            "department_column": None,
            "headcount_column": None,
        }

        columns_lower = {col: col.lower() for col in columns}

        for col, col_lower in columns_lower.items():
            if suggestions["role_column"] is None:
                if any(keyword in col_lower for keyword in self._ROLE_KEYWORDS):
                    suggestions["role_column"] = col

            if suggestions["department_column"] is None:
                if any(keyword in col_lower for keyword in self._DEPARTMENT_KEYWORDS):
                    suggestions["department_column"] = col

            if suggestions["headcount_column"] is None:
                if any(keyword in col_lower for keyword in self._HEADCOUNT_KEYWORDS):
                    suggestions["headcount_column"] = col

        return suggestions

    async def process(self, message: str) -> dict[str, Any]:
        """Process an incoming message and return a response.

        Implements a brainstorming-style interaction where the agent
        asks one clarifying question at a time.

        Args:
            message: The input message to process.

        Returns:
            A structured response dictionary with question/message and choices.
        """
        # If there's a pending question, process the user's answer
        if self._pending_question:
            return await self._handle_column_selection(message)

        # If file is uploaded, start the column mapping process
        if self._file_uploaded and self._columns:
            return await self._ask_for_column_mapping()

        # Default response when no file is uploaded
        return self.format_response(
            message="Please upload a file to begin.",
            question="Would you like to upload a CSV or Excel file?",
            choices=["Upload CSV", "Upload Excel"],
        )

    async def _ask_for_column_mapping(self) -> dict[str, Any]:
        """Ask the user to confirm or select a column mapping.

        Returns:
            A response with the next column mapping question.
        """
        # Determine which mapping to ask about next
        for mapping_key in self._MAPPING_ORDER:
            if mapping_key not in self._column_mappings:
                self._pending_question = mapping_key
                question = self._get_question_for_mapping(mapping_key)
                # Limit choices to at most 5
                choices = self._columns[:5]
                return self.format_response(
                    message=question,
                    question=question,
                    choices=choices,
                )

        # All mappings complete
        return self.format_response(
            message="Column mapping complete!",
            choices=[],
        )

    def _get_question_for_mapping(self, mapping_key: str) -> str:
        """Get the question text for a specific mapping key.

        Args:
            mapping_key: The mapping key to get a question for.

        Returns:
            The question text.
        """
        questions = {
            "role_column": "Which column contains the role or job title?",
            "department_column": "Which column contains the department?",
            "headcount_column": "Which column contains the headcount?",
        }
        return questions.get(mapping_key, "Please select a column.")

    async def _handle_column_selection(self, selected_column: str) -> dict[str, Any]:
        """Handle the user's column selection for a pending question.

        Args:
            selected_column: The column name selected by the user.

        Returns:
            A response confirming the selection and asking the next question.
        """
        if self._pending_question:
            # Validate that selected column exists in the available columns
            if selected_column not in self._columns:
                return self.format_response(
                    message=f"'{selected_column}' is not a valid column. Please select from the available columns.",
                    question=self._get_question_for_mapping(self._pending_question),
                    choices=self._columns[:5],
                )

            self._column_mappings[self._pending_question] = selected_column
            confirmed_mapping = self._pending_question
            self._pending_question = None

            # Check if there are more mappings to complete
            for mapping_key in self._MAPPING_ORDER:
                if mapping_key not in self._column_mappings:
                    # Ask next question
                    self._pending_question = mapping_key
                    question = self._get_question_for_mapping(mapping_key)
                    choices = self._columns[:5]
                    return self.format_response(
                        message=f"Got it! {selected_column} will be used for {confirmed_mapping}.",
                        confirmed_value=selected_column,
                        question=question,
                        choices=choices,
                    )

            # All mappings complete
            return self.format_response(
                message=f"Got it! {selected_column} confirmed. All column mappings are complete!",
                confirmed_value=selected_column,
                choices=[],
            )

        return self.format_response(
            message="No pending question to answer.",
            choices=[],
        )
