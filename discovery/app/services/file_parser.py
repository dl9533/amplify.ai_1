# discovery/app/services/file_parser.py
"""File parser for CSV and Excel files."""
import io
import re
from typing import Any

import pandas as pd


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

    def parse(self, content: bytes, filename: str) -> dict[str, Any]:
        """Parse file content and extract schema.

        Args:
            content: File content as bytes.
            filename: Original filename (for extension detection).

        Returns:
            Dict with row_count, detected_schema, column_suggestions, preview.
        """
        ext = filename.lower().split(".")[-1]

        if ext == "csv":
            df = pd.read_csv(io.BytesIO(content))
        elif ext in ("xlsx", "xls"):
            df = pd.read_excel(io.BytesIO(content))
        else:
            raise ValueError(f"Unsupported file type: {ext}")

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
        """
        ext = filename.lower().split(".")[-1]

        if ext == "csv":
            df = pd.read_csv(io.BytesIO(content))
        else:
            df = pd.read_excel(io.BytesIO(content))

        value_counts = df[column].value_counts()
        return [
            {"value": str(val), "count": int(count)}
            for val, count in value_counts.items()
        ]
