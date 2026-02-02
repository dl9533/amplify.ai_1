# discovery/tests/unit/services/test_file_parser.py
"""Unit tests for file parser."""
import pytest
import io


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
