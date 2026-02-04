"""Column detection service for auto-detecting field mappings in uploaded files."""
from dataclasses import dataclass
from typing import Any


@dataclass
class DetectedMapping:
    """Result of column detection for a field."""

    field: str
    column: str | None
    confidence: float
    alternatives: list[str]
    required: bool


class ColumnDetectionService:
    """Auto-detect column mappings using heuristics + LLM fallback.

    Detects which columns in an uploaded file correspond to:
    - role: Job title, position, or occupation
    - lob: Line of business, business unit, segment
    - department: Department, cost center, or team
    - geography: Office location, city, region
    """

    FIELD_DEFINITIONS = {
        "role": {
            "description": "Job title, position, or role name",
            "keywords": ["title", "position", "role", "job", "occupation", "designation"],
            "required": True,
        },
        "lob": {
            "description": "Line of business, business unit, segment, or division",
            "keywords": ["lob", "line of business", "business unit", "segment", "division", "business line"],
            "required": False,
        },
        "department": {
            "description": "Department, cost center, or team",
            "keywords": ["department", "dept", "cost center", "team", "group", "function", "org"],
            "required": False,
        },
        "geography": {
            "description": "Office location, city, region, or site",
            "keywords": ["location", "office", "site", "region", "city", "geo", "country"],
            "required": False,
        },
    }

    def __init__(self, llm_service: Any = None):
        """Initialize service with optional LLM for fallback.

        Args:
            llm_service: Optional LLM service for detecting ambiguous columns.
        """
        self.llm_service = llm_service

    def detect_mappings_sync(
        self,
        columns: list[str],
        sample_rows: list[dict],
    ) -> list[DetectedMapping]:
        """Synchronously detect column mappings (no LLM fallback).

        Args:
            columns: List of column names from the uploaded file.
            sample_rows: Sample data rows for pattern analysis.

        Returns:
            List of DetectedMapping for each field type.
        """
        return self._detect_with_keywords(columns, sample_rows)

    async def detect_mappings(
        self,
        columns: list[str],
        sample_rows: list[dict],
    ) -> list[DetectedMapping]:
        """Detect column mappings with LLM fallback for ambiguous cases.

        Args:
            columns: List of column names from the uploaded file.
            sample_rows: Sample data rows for pattern analysis.

        Returns:
            List of DetectedMapping for each field type.
        """
        mappings = self._detect_with_keywords(columns, sample_rows)

        # Use LLM fallback for low-confidence required fields
        if self.llm_service:
            for mapping in mappings:
                if mapping.required and mapping.confidence < 0.6:
                    llm_result = await self._llm_detect(
                        mapping.field,
                        columns,
                        sample_rows,
                    )
                    if llm_result:
                        mapping.column = llm_result.column
                        mapping.confidence = llm_result.confidence

        return mappings

    def _detect_with_keywords(
        self,
        columns: list[str],
        sample_rows: list[dict],
    ) -> list[DetectedMapping]:
        """Detect mappings using keyword matching.

        Args:
            columns: List of column names.
            sample_rows: Sample data rows (unused in keyword matching).

        Returns:
            List of DetectedMapping for each field.
        """
        mappings = []
        used_columns: set[str] = set()

        for field, definition in self.FIELD_DEFINITIONS.items():
            match = self._keyword_match(
                columns,
                definition["keywords"],
                used_columns,
            )

            alternatives = [c for c in columns if c not in used_columns]

            if match:
                mappings.append(
                    DetectedMapping(
                        field=field,
                        column=match["column"],
                        confidence=match["confidence"],
                        alternatives=alternatives,
                        required=definition["required"],
                    )
                )
                used_columns.add(match["column"])
            else:
                mappings.append(
                    DetectedMapping(
                        field=field,
                        column=None,
                        confidence=0.0,
                        alternatives=alternatives,
                        required=definition["required"],
                    )
                )

        return mappings

    def _keyword_match(
        self,
        columns: list[str],
        keywords: list[str],
        used: set[str],
    ) -> dict | None:
        """Match column to keywords with confidence scoring.

        Args:
            columns: List of column names.
            keywords: Keywords to match against.
            used: Set of already-used column names.

        Returns:
            Dict with column and confidence, or None if no match.
        """
        best_match = None
        best_score = 0.0

        for col in columns:
            if col in used:
                continue

            col_lower = col.lower().strip()

            for keyword in keywords:
                keyword_lower = keyword.lower()

                # Exact match
                if col_lower == keyword_lower:
                    return {"column": col, "confidence": 1.0}

                # Contains keyword (e.g., "Job Title" contains "title")
                if keyword_lower in col_lower:
                    score = 0.9
                    if score > best_score:
                        best_score = score
                        best_match = {"column": col, "confidence": score}

                # Column is substring of keyword (e.g., "Dept" in "department")
                elif col_lower in keyword_lower and len(col_lower) >= 3:
                    score = 0.8
                    if score > best_score:
                        best_score = score
                        best_match = {"column": col, "confidence": score}

        return best_match if best_score >= 0.8 else None

    async def _llm_detect(
        self,
        field: str,
        columns: list[str],
        sample_rows: list[dict],
    ) -> DetectedMapping | None:
        """Use LLM to detect column mapping for ambiguous cases.

        Args:
            field: The field type to detect.
            columns: List of column names.
            sample_rows: Sample data rows for context.

        Returns:
            DetectedMapping if LLM identifies a match, None otherwise.
        """
        if not self.llm_service:
            return None

        definition = self.FIELD_DEFINITIONS[field]
        prompt = f"""Given these columns and sample data, identify which column contains the {field}.

Field description: {definition['description']}

Columns: {columns}

Sample data:
{sample_rows[:3]}

Respond with just the column name, or "NONE" if no match."""

        response = await self.llm_service.complete(prompt)
        col = response.strip()

        if col in columns:
            return DetectedMapping(
                field=field,
                column=col,
                confidence=0.7,  # LLM confidence
                alternatives=[],
                required=definition["required"],
            )

        return None
