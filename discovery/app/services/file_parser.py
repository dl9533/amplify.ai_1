# discovery/app/services/file_parser.py
"""File parser for CSV and Excel files."""
import io
import re
from pathlib import Path
from typing import Any

import pandas as pd

from app.exceptions import FileParseException


class FileParser:
    """Parses uploaded files and detects schema."""

    # Patterns for column detection
    ROLE_PATTERNS = [
        r"(?i)^(job[_\s]?title|role|position|occupation|title)$",
        r"(?i).*job[_\s]?title.*",
        r"(?i).*role.*",
    ]
    DEPARTMENT_PATTERNS = [
        r"(?i)^(department|dept|division|team|unit)$",
        r"(?i).*department.*",
        r"(?i).*dept.*",
    ]
    GEOGRAPHY_PATTERNS = [
        r"(?i)^(location|city|region|country|office|site)$",
        r"(?i).*location.*",
        r"(?i).*geography.*",
    ]

    # Allowed file extensions
    ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls"}

    def parse(self, content: bytes, filename: str) -> dict[str, Any]:
        """Parse file content and extract schema.

        Args:
            content: File content as bytes.
            filename: Original filename (for extension detection).

        Returns:
            Dict with row_count, detected_schema, column_suggestions, preview.

        Raises:
            FileParseException: If file type is unsupported or parsing fails.
        """
        ext = self._get_safe_extension(filename)

        if ext not in self.ALLOWED_EXTENSIONS:
            raise FileParseException(
                f"Unsupported file type: {ext}. Allowed types: {', '.join(self.ALLOWED_EXTENSIONS)}",
                filename=filename,
            )

        try:
            if ext == "csv":
                df = pd.read_csv(io.BytesIO(content))
            else:  # xlsx, xls
                df = pd.read_excel(io.BytesIO(content))
        except Exception as e:
            raise FileParseException(
                f"Failed to parse file: {e}",
                filename=filename,
            ) from e

        columns = self._detect_columns(df)
        suggestions = self._suggest_mappings(df.columns.tolist())

        return {
            "row_count": len(df),
            "detected_schema": {
                "columns": columns,
                "dtypes": {col: str(df[col].dtype) for col in df.columns},
            },
            "column_suggestions": suggestions,
            "preview": df.head(5).to_dict(orient="records"),
        }

    def _detect_columns(self, df: pd.DataFrame) -> list[dict[str, Any]]:
        """Detect column types and sample values."""
        columns = []
        for col in df.columns:
            sample_values = df[col].dropna().head(3).tolist()
            columns.append({
                "name": col,
                "dtype": str(df[col].dtype),
                "null_count": int(df[col].isna().sum()),
                "unique_count": int(df[col].nunique()),
                "sample_values": sample_values,
            })
        return columns

    def _suggest_mappings(self, column_names: list[str]) -> dict[str, str | None]:
        """Suggest column mappings based on patterns."""
        suggestions: dict[str, str | None] = {
            "role": None,
            "department": None,
            "geography": None,
        }

        for col in column_names:
            for pattern in self.ROLE_PATTERNS:
                if re.match(pattern, col) and suggestions["role"] is None:
                    suggestions["role"] = col
                    break

            for pattern in self.DEPARTMENT_PATTERNS:
                if re.match(pattern, col) and suggestions["department"] is None:
                    suggestions["department"] = col
                    break

            for pattern in self.GEOGRAPHY_PATTERNS:
                if re.match(pattern, col) and suggestions["geography"] is None:
                    suggestions["geography"] = col
                    break

        return suggestions

    def extract_unique_values(
        self,
        content: bytes,
        filename: str,
        column: str,
    ) -> list[dict[str, Any]]:
        """Extract unique values from a column with counts.

        Args:
            content: File content.
            filename: Original filename.
            column: Column name to extract.

        Returns:
            List of dicts with value and count.

        Raises:
            FileParseException: If column doesn't exist or file can't be parsed.
        """
        ext = self._get_safe_extension(filename)

        try:
            if ext == "csv":
                df = pd.read_csv(io.BytesIO(content))
            else:
                df = pd.read_excel(io.BytesIO(content))
        except Exception as e:
            raise FileParseException(
                f"Failed to parse file: {e}",
                filename=filename,
            ) from e

        # Validate column exists
        if column not in df.columns:
            available_columns = ", ".join(df.columns.tolist())
            raise FileParseException(
                f"Column '{column}' not found in file. Available columns: {available_columns}",
                filename=filename,
            )

        value_counts = df[column].value_counts()
        return [
            {"value": str(val), "count": int(count)}
            for val, count in value_counts.items()
        ]

    def _get_safe_extension(self, filename: str) -> str:
        """Safely extract file extension.

        Uses pathlib to properly handle edge cases like multiple dots,
        no extension, or path traversal attempts.

        Args:
            filename: Original filename.

        Returns:
            Lowercase file extension without the dot.
        """
        # Use pathlib for safe extension extraction
        path = Path(filename)
        ext = path.suffix.lower().lstrip(".")

        # If no extension, return empty string
        if not ext:
            return ""

        return ext
