# discovery/app/agents/upload_agent.py
"""Upload subagent for Step 1: File Upload."""
from typing import Any, Optional
from uuid import UUID

from app.agents.base import BaseSubagent
from app.services.upload_service import UploadService


class UploadSubagent(BaseSubagent):
    """Handles file upload, schema detection, and column mapping."""

    agent_type: str = "upload"

    def __init__(
        self,
        session: Any,
        upload_service: UploadService,
        memory_service: Any = None,
    ) -> None:
        super().__init__(session, memory_service)
        self.upload_service = upload_service
        self._awaiting_confirmation = False
        self._pending_mappings: dict[str, Optional[str]] = {}
        self._current_upload_id: Optional[str] = None

    async def process(self, message: str) -> dict[str, Any]:
        """Process user message for upload step."""
        message_lower = message.lower()

        # Check for upload status
        uploads = await self.upload_service.get_by_session_id(self.session.id)

        if not uploads:
            return {
                "message": "Please upload your workforce data file (.xlsx or .csv) to begin.",
                "quick_actions": ["Upload file"],
                "step_complete": False,
            }

        upload = uploads[0]  # Use most recent
        self._current_upload_id = upload.get("id")
        schema = upload.get("detected_schema", {})
        suggestions = upload.get("column_suggestions", {})
        row_count = upload.get("row_count", 0)

        # If awaiting confirmation
        if self._awaiting_confirmation:
            if any(word in message_lower for word in ["yes", "confirm", "correct", "looks good"]):
                await self.upload_service.update_column_mappings(
                    UUID(self._current_upload_id),
                    self._pending_mappings,
                )
                return {
                    "message": "Column mappings confirmed. Moving to role mapping step.",
                    "quick_actions": [],
                    "step_complete": True,
                }
            elif any(word in message_lower for word in ["no", "change", "different"]):
                self._awaiting_confirmation = False
                return {
                    "message": "Which column contains job titles/roles?",
                    "quick_actions": [c["name"] for c in schema.get("columns", [])[:5]],
                    "step_complete": False,
                }

        # Check if user is specifying a column
        columns = [c["name"] for c in schema.get("columns", [])]
        for col in columns:
            if col.lower() in message_lower:
                if not self._pending_mappings.get("role"):
                    self._pending_mappings["role"] = col
                    other_cols = [c for c in columns if c != col][:4]
                    other_cols.append("Skip")
                    return {
                        "message": f"Got it, '{col}' contains roles. Which column has department/team info?",
                        "quick_actions": other_cols,
                        "step_complete": False,
                    }
                elif not self._pending_mappings.get("department"):
                    self._pending_mappings["department"] = col if col.lower() != "skip" else None
                    self._awaiting_confirmation = True
                    dept_display = self._pending_mappings.get("department") or "None"
                    return {
                        "message": f"I'll use:\n- Roles: {self._pending_mappings['role']}\n- Department: {dept_display}\n\nIs this correct?",
                        "quick_actions": ["Yes, continue", "No, let me change"],
                        "step_complete": False,
                    }

        # Handle skip for department
        if "skip" in message_lower and self._pending_mappings.get("role"):
            self._pending_mappings["department"] = None
            self._awaiting_confirmation = True
            return {
                "message": f"I'll use:\n- Roles: {self._pending_mappings['role']}\n- Department: None\n\nIs this correct?",
                "quick_actions": ["Yes, continue", "No, let me change"],
                "step_complete": False,
            }

        # Default: Show detected schema and ask for confirmation
        if suggestions.get("role"):
            self._pending_mappings = {
                "role": suggestions.get("role"),
                "department": suggestions.get("department"),
                "geography": suggestions.get("geography"),
            }
            self._awaiting_confirmation = True

            role_col = suggestions.get("role", "unknown")
            dept_col = suggestions.get("department", "none detected")
            return {
                "message": f"I analyzed your file and found:\n- {row_count} rows\n- Role column: '{role_col}'\n- Department: '{dept_col}'\n\nDoes this look correct?",
                "quick_actions": ["Yes, continue", "No, let me specify"],
                "step_complete": False,
            }

        # No suggestions - ask user
        return {
            "message": "I found these columns in your file. Which one contains job titles/roles?",
            "quick_actions": columns[:5],
            "step_complete": False,
        }
