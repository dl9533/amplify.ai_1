"""Unit tests for UploadSubagent."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.agents.upload_agent import UploadSubagent
from app.agents.base import BaseSubagent


@pytest.fixture
def upload_agent():
    """Create an UploadSubagent instance for testing."""
    return UploadSubagent(
        session=MagicMock(id=uuid4()),
        memory_service=AsyncMock(),
    )


class TestUploadSubagentSetup:
    """Tests for upload agent configuration."""

    def test_upload_agent_extends_base_subagent(self, upload_agent):
        """UploadSubagent should extend BaseSubagent."""
        assert isinstance(upload_agent, BaseSubagent)

    def test_upload_agent_type_is_upload(self, upload_agent):
        """Agent type should be 'upload'."""
        assert upload_agent.agent_type == "upload"


class TestColumnDetection:
    """Tests for file column detection."""

    @pytest.mark.asyncio
    async def test_detect_columns_from_csv(self, upload_agent):
        """Should detect column names from uploaded CSV."""
        file_content = "Name,Department,Role\nJohn,Engineering,Developer"

        result = await upload_agent.detect_columns(file_content, file_type="csv")

        assert "Name" in result
        assert "Department" in result
        assert "Role" in result

    @pytest.mark.asyncio
    async def test_suggest_column_mappings(self, upload_agent):
        """Should suggest which columns map to required fields."""
        columns = ["Employee Name", "Dept", "Job Title", "Location", "Headcount"]

        result = await upload_agent.suggest_column_mappings(columns)

        assert "role_column" in result
        assert "department_column" in result
        assert "headcount_column" in result


class TestBrainstormingInteraction:
    """Tests for brainstorming-style interactions."""

    @pytest.mark.asyncio
    async def test_process_asks_one_question_at_time(self, upload_agent):
        """Should ask one clarifying question at a time."""
        upload_agent._file_uploaded = True
        upload_agent._columns = ["Name", "Title", "Dept"]

        response = await upload_agent.process("I uploaded the file")

        assert response.get("question") is not None or response.get("message") is not None
        assert response.get("choices") is not None
        assert len(response.get("choices", [])) <= 5  # Max 5 choices

    @pytest.mark.asyncio
    async def test_process_confirms_column_selection(self, upload_agent):
        """Should confirm user's column selection."""
        upload_agent._file_uploaded = True
        upload_agent._pending_question = "role_column"

        response = await upload_agent.process("Job Title")

        assert "Job Title" in str(response) or response.get("confirmed_value") == "Job Title"
