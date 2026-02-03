"""Unit tests for O*NET sync log model."""
import pytest
from sqlalchemy import inspect

from app.models.onet_occupation import OnetSyncLog


class TestOnetSyncLogModel:
    """Tests for OnetSyncLog SQLAlchemy model."""

    def test_model_has_correct_tablename(self):
        """Model should have correct table name."""
        assert OnetSyncLog.__tablename__ == "onet_sync_log"

    def test_model_has_required_columns(self):
        """Model should have all required columns."""
        mapper = inspect(OnetSyncLog)
        column_names = [col.name for col in mapper.columns]
        assert "id" in column_names
        assert "version" in column_names
        assert "synced_at" in column_names
        assert "occupation_count" in column_names
        assert "status" in column_names

    def test_model_has_uuid_primary_key(self):
        """Model should have UUID id as primary key."""
        mapper = inspect(OnetSyncLog)
        pk_columns = [col.name for col in mapper.primary_key]
        assert pk_columns == ["id"]

    def test_model_has_count_columns(self):
        """Model should have count columns for tracking sync stats."""
        mapper = inspect(OnetSyncLog)
        column_names = [col.name for col in mapper.columns]
        assert "alternate_title_count" in column_names
        assert "task_count" in column_names
