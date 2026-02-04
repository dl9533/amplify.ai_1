# discovery/tests/unit/services/test_file_parser.py
"""Unit tests for file parser."""
import pytest
import io

from app.exceptions import FileParseException


def test_file_parser_exists():
    """Test FileParser is importable."""
    from app.services.file_parser import FileParser
    assert FileParser is not None


def test_parse_csv():
    """Test parsing CSV content."""
    from app.services.file_parser import FileParser

    csv_content = b"name,role,department\nJohn,Engineer,IT\nJane,Analyst,Finance"
    parser = FileParser()
    result = parser.parse(csv_content, "test.csv")

    assert result["row_count"] == 2
    assert "columns" in result["detected_schema"]
    assert len(result["detected_schema"]["columns"]) == 3


def test_parse_xlsx():
    """Test parsing Excel content."""
    from app.services.file_parser import FileParser

    # Create minimal xlsx in memory
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["name", "role", "department"])
    ws.append(["John", "Engineer", "IT"])

    buffer = io.BytesIO()
    wb.save(buffer)
    xlsx_content = buffer.getvalue()

    parser = FileParser()
    result = parser.parse(xlsx_content, "test.xlsx")

    assert result["row_count"] == 1
    assert "columns" in result["detected_schema"]


def test_detect_role_column():
    """Test automatic role column detection."""
    from app.services.file_parser import FileParser

    csv_content = b"employee_name,job_title,dept\nJohn,Software Engineer,IT"
    parser = FileParser()
    result = parser.parse(csv_content, "test.csv")

    suggestions = result.get("column_suggestions", {})
    assert "role" in suggestions
    assert suggestions["role"] == "job_title"


class TestColumnValidation:
    """Test column validation in extract_unique_values."""

    def test_extract_unique_values_missing_column_raises(self):
        """Test missing column raises FileParseException."""
        from app.services.file_parser import FileParser

        parser = FileParser()
        content = b"Name,Age\nJohn,30\nJane,25"

        with pytest.raises(FileParseException, match="not found"):
            parser.extract_unique_values(content, "test.csv", "NonExistent")

    def test_extract_unique_values_missing_column_lists_available(self):
        """Test error message lists available columns."""
        from app.services.file_parser import FileParser

        parser = FileParser()
        content = b"Name,Age,City\nJohn,30,NYC"

        try:
            parser.extract_unique_values(content, "test.csv", "Missing")
            assert False, "Should have raised FileParseException"
        except FileParseException as e:
            assert "Name" in str(e.message)
            assert "Age" in str(e.message)
            assert "City" in str(e.message)

    def test_extract_unique_values_valid_column_works(self):
        """Test valid column extraction works."""
        from app.services.file_parser import FileParser

        parser = FileParser()
        content = b"Name,Age\nJohn,30\nJane,25\nJohn,35"

        result = parser.extract_unique_values(content, "test.csv", "Name")

        assert len(result) == 2
        values = {r["value"] for r in result}
        assert "John" in values
        assert "Jane" in values


class TestSafeExtensionExtraction:
    """Test safe file extension extraction."""

    def test_get_safe_extension_simple(self):
        """Test simple extension extraction."""
        from app.services.file_parser import FileParser

        parser = FileParser()

        assert parser._get_safe_extension("file.csv") == "csv"
        assert parser._get_safe_extension("file.xlsx") == "xlsx"
        assert parser._get_safe_extension("file.xls") == "xls"

    def test_get_safe_extension_uppercase(self):
        """Test uppercase extension is lowercased."""
        from app.services.file_parser import FileParser

        parser = FileParser()

        assert parser._get_safe_extension("file.CSV") == "csv"
        assert parser._get_safe_extension("file.XLSX") == "xlsx"

    def test_get_safe_extension_multiple_dots(self):
        """Test filename with multiple dots."""
        from app.services.file_parser import FileParser

        parser = FileParser()

        # Should get the last extension only
        assert parser._get_safe_extension("my.data.file.csv") == "csv"

    def test_get_safe_extension_no_extension(self):
        """Test filename without extension."""
        from app.services.file_parser import FileParser

        parser = FileParser()

        assert parser._get_safe_extension("noextension") == ""

    def test_get_safe_extension_path_traversal(self):
        """Test extension extraction ignores path traversal."""
        from app.services.file_parser import FileParser

        parser = FileParser()

        # pathlib.Path.name extracts just the filename
        assert parser._get_safe_extension("../../../etc/passwd.csv") == "csv"


class TestUnsupportedFileType:
    """Test unsupported file type handling."""

    def test_parse_unsupported_extension_raises(self):
        """Test unsupported file extension raises FileParseException."""
        from app.services.file_parser import FileParser

        parser = FileParser()

        with pytest.raises(FileParseException, match="Unsupported file type"):
            parser.parse(b"some content", "file.txt")

    def test_parse_unsupported_lists_allowed_types(self):
        """Test error message lists allowed types."""
        from app.services.file_parser import FileParser

        parser = FileParser()

        try:
            parser.parse(b"some content", "file.pdf")
            assert False, "Should have raised FileParseException"
        except FileParseException as e:
            assert "csv" in str(e.message)
            assert "xlsx" in str(e.message)
            assert "xls" in str(e.message)
