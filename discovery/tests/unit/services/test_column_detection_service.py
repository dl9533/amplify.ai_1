"""Test ColumnDetectionService."""
import pytest
from app.services.column_detection_service import ColumnDetectionService, DetectedMapping


@pytest.fixture
def service():
    return ColumnDetectionService()


class TestKeywordMatching:
    """Test keyword-based column detection."""

    def test_detect_role_column_from_title(self, service):
        """Test detecting role column from 'Job Title' header."""
        columns = ["Employee ID", "Job Title", "Department"]
        sample_rows = [
            {"Employee ID": "1001", "Job Title": "Software Engineer", "Department": "IT"},
        ]

        result = service.detect_mappings_sync(columns, sample_rows)
        role_mapping = next((m for m in result if m.field == "role"), None)

        assert role_mapping is not None
        assert role_mapping.column == "Job Title"
        assert role_mapping.confidence >= 0.8

    def test_detect_lob_column(self, service):
        """Test detecting LOB column."""
        columns = ["Name", "Line of Business", "Title"]
        sample_rows = [
            {"Name": "John", "Line of Business": "Retail Banking", "Title": "Analyst"},
        ]

        result = service.detect_mappings_sync(columns, sample_rows)
        lob_mapping = next((m for m in result if m.field == "lob"), None)

        assert lob_mapping is not None
        assert lob_mapping.column == "Line of Business"
        assert lob_mapping.confidence >= 0.8

    def test_detect_department_column(self, service):
        """Test detecting department column."""
        columns = ["Emp", "Dept", "Role"]
        sample_rows = [{"Emp": "1", "Dept": "Finance", "Role": "Manager"}]

        result = service.detect_mappings_sync(columns, sample_rows)
        dept_mapping = next((m for m in result if m.field == "department"), None)

        assert dept_mapping is not None
        assert dept_mapping.column == "Dept"

    def test_detect_geography_column(self, service):
        """Test detecting geography/location column."""
        columns = ["Name", "Office Location", "Team"]
        sample_rows = [{"Name": "Jane", "Office Location": "New York", "Team": "Sales"}]

        result = service.detect_mappings_sync(columns, sample_rows)
        geo_mapping = next((m for m in result if m.field == "geography"), None)

        assert geo_mapping is not None
        assert geo_mapping.column == "Office Location"

    def test_no_match_returns_alternatives(self, service):
        """Test that unmatched columns provide alternatives."""
        columns = ["A", "B", "C"]  # Ambiguous names
        sample_rows = [{"A": "1", "B": "2", "C": "3"}]

        result = service.detect_mappings_sync(columns, sample_rows)
        role_mapping = next((m for m in result if m.field == "role"), None)

        assert role_mapping is not None
        assert role_mapping.column is None or role_mapping.confidence < 0.6
        assert len(role_mapping.alternatives) > 0

    def test_role_is_marked_required(self, service):
        """Test that role field is marked as required."""
        columns = ["Name", "Position"]
        sample_rows = [{"Name": "John", "Position": "Manager"}]

        result = service.detect_mappings_sync(columns, sample_rows)
        role_mapping = next((m for m in result if m.field == "role"), None)

        assert role_mapping.required is True

    def test_lob_is_not_required(self, service):
        """Test that LOB field is not marked as required."""
        columns = ["Name", "Business Unit"]
        sample_rows = [{"Name": "John", "Business Unit": "Retail"}]

        result = service.detect_mappings_sync(columns, sample_rows)
        lob_mapping = next((m for m in result if m.field == "lob"), None)

        assert lob_mapping.required is False

    def test_returns_all_field_types(self, service):
        """Test that all four field types are returned."""
        columns = ["A"]
        sample_rows = [{"A": "1"}]

        result = service.detect_mappings_sync(columns, sample_rows)
        fields = {m.field for m in result}

        assert fields == {"role", "lob", "department", "geography"}

    def test_exact_match_has_highest_confidence(self, service):
        """Test that exact keyword match returns confidence 1.0."""
        columns = ["Title", "Department"]
        sample_rows = [{"Title": "Engineer", "Department": "IT"}]

        result = service.detect_mappings_sync(columns, sample_rows)
        role_mapping = next((m for m in result if m.field == "role"), None)

        assert role_mapping.column == "Title"
        assert role_mapping.confidence == 1.0

    def test_columns_not_reused(self, service):
        """Test that each column is only used once."""
        columns = ["Job Title", "Title"]  # Both could match role
        sample_rows = [{"Job Title": "Engineer", "Title": "Sr."}]

        result = service.detect_mappings_sync(columns, sample_rows)

        used_columns = [m.column for m in result if m.column is not None]
        assert len(used_columns) == len(set(used_columns))  # No duplicates
