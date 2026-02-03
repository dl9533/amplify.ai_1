"""Unit tests for O*NET occupation model."""
import pytest
from sqlalchemy import inspect

from app.models.onet_occupation import OnetOccupation


class TestOnetOccupationModel:
    """Tests for OnetOccupation SQLAlchemy model."""

    def test_model_has_correct_tablename(self):
        """Model should have correct table name."""
        assert OnetOccupation.__tablename__ == "onet_occupations"

    def test_model_has_code_primary_key(self):
        """Model should have code as primary key."""
        mapper = inspect(OnetOccupation)
        pk_columns = [col.name for col in mapper.primary_key]
        assert pk_columns == ["code"]

    def test_model_has_required_columns(self):
        """Model should have all required columns."""
        mapper = inspect(OnetOccupation)
        column_names = [col.name for col in mapper.columns]
        assert "code" in column_names
        assert "title" in column_names
        assert "description" in column_names
        assert "updated_at" in column_names

    def test_model_code_max_length(self):
        """Code column should have max length of 10."""
        mapper = inspect(OnetOccupation)
        code_col = mapper.columns["code"]
        assert code_col.type.length == 10

    def test_model_title_not_nullable(self):
        """Title column should not be nullable."""
        mapper = inspect(OnetOccupation)
        title_col = mapper.columns["title"]
        assert title_col.nullable is False
