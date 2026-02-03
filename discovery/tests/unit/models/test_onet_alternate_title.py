"""Unit tests for O*NET alternate title model."""
import pytest
from sqlalchemy import inspect

from app.models.onet_occupation import OnetAlternateTitle


class TestOnetAlternateTitleModel:
    """Tests for OnetAlternateTitle SQLAlchemy model."""

    def test_model_has_correct_tablename(self):
        """Model should have correct table name."""
        assert OnetAlternateTitle.__tablename__ == "onet_alternate_titles"

    def test_model_has_uuid_primary_key(self):
        """Model should have UUID id as primary key."""
        mapper = inspect(OnetAlternateTitle)
        pk_columns = [col.name for col in mapper.primary_key]
        assert pk_columns == ["id"]

    def test_model_has_onet_code_foreign_key(self):
        """Model should have onet_code foreign key."""
        mapper = inspect(OnetAlternateTitle)
        column_names = [col.name for col in mapper.columns]
        assert "onet_code" in column_names

        fk_cols = list(mapper.columns["onet_code"].foreign_keys)
        assert len(fk_cols) == 1
        assert "onet_occupations.code" in str(fk_cols[0])

    def test_model_has_title_column(self):
        """Model should have title column."""
        mapper = inspect(OnetAlternateTitle)
        assert "title" in [col.name for col in mapper.columns]
        assert mapper.columns["title"].nullable is False
