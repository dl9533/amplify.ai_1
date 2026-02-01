"""Integration tests for agent memory migration.

These tests verify that the agent memory tables are correctly created by the
migration script for the three-tier memory hierarchy used by discovery subagents.
"""

import pytest
from sqlalchemy import inspect


@pytest.mark.asyncio
async def test_agent_memory_working_table_exists(db_engine):
    """agent_memory_working table should exist after migration."""
    async with db_engine.connect() as conn:
        def get_tables(connection):
            inspector = inspect(connection)
            return inspector.get_table_names()

        tables = await conn.run_sync(get_tables)
        assert "agent_memory_working" in tables


@pytest.mark.asyncio
async def test_agent_memory_episodic_table_exists(db_engine):
    """agent_memory_episodic table should exist after migration."""
    async with db_engine.connect() as conn:
        def get_tables(connection):
            inspector = inspect(connection)
            return inspector.get_table_names()

        tables = await conn.run_sync(get_tables)
        assert "agent_memory_episodic" in tables


@pytest.mark.asyncio
async def test_agent_memory_semantic_table_exists(db_engine):
    """agent_memory_semantic table should exist after migration."""
    async with db_engine.connect() as conn:
        def get_tables(connection):
            inspector = inspect(connection)
            return inspector.get_table_names()

        tables = await conn.run_sync(get_tables)
        assert "agent_memory_semantic" in tables


@pytest.mark.asyncio
async def test_agent_memory_working_columns(db_engine):
    """agent_memory_working should have all required columns."""
    async with db_engine.connect() as conn:
        def get_columns(connection):
            inspector = inspect(connection)
            return {col["name"] for col in inspector.get_columns("agent_memory_working")}

        columns = await conn.run_sync(get_columns)
        expected_columns = {
            "id",
            "agent_type",
            "session_id",
            "context",
            "expires_at",
            "created_at",
            "updated_at",
        }
        assert expected_columns.issubset(columns)


@pytest.mark.asyncio
async def test_agent_memory_episodic_columns(db_engine):
    """agent_memory_episodic should have all required columns."""
    async with db_engine.connect() as conn:
        def get_columns(connection):
            inspector = inspect(connection)
            return {col["name"] for col in inspector.get_columns("agent_memory_episodic")}

        columns = await conn.run_sync(get_columns)
        expected_columns = {
            "id",
            "agent_type",
            "organization_id",
            "episode_type",
            "content",
            "relevance_score",
            "created_at",
            "updated_at",
        }
        assert expected_columns.issubset(columns)


@pytest.mark.asyncio
async def test_agent_memory_semantic_columns(db_engine):
    """agent_memory_semantic should have all required columns."""
    async with db_engine.connect() as conn:
        def get_columns(connection):
            inspector = inspect(connection)
            return {col["name"] for col in inspector.get_columns("agent_memory_semantic")}

        columns = await conn.run_sync(get_columns)
        expected_columns = {
            "id",
            "agent_type",
            "organization_id",
            "fact_type",
            "content",
            "confidence",
            "occurrence_count",
            "last_updated",
            "created_at",
            "updated_at",
        }
        assert expected_columns.issubset(columns)


@pytest.mark.asyncio
async def test_agent_memory_working_has_indexes(db_engine):
    """agent_memory_working should have indexes on agent_type and session_id."""
    async with db_engine.connect() as conn:
        def get_indexes(connection):
            inspector = inspect(connection)
            return inspector.get_indexes("agent_memory_working")

        indexes = await conn.run_sync(get_indexes)
        indexed_columns = set()
        for idx in indexes:
            indexed_columns.update(idx["column_names"])

        assert "agent_type" in indexed_columns
        assert "session_id" in indexed_columns


@pytest.mark.asyncio
async def test_agent_memory_episodic_has_indexes(db_engine):
    """agent_memory_episodic should have indexes on key columns."""
    async with db_engine.connect() as conn:
        def get_indexes(connection):
            inspector = inspect(connection)
            return inspector.get_indexes("agent_memory_episodic")

        indexes = await conn.run_sync(get_indexes)
        indexed_columns = set()
        for idx in indexes:
            indexed_columns.update(idx["column_names"])

        assert "agent_type" in indexed_columns
        assert "organization_id" in indexed_columns
        assert "episode_type" in indexed_columns


@pytest.mark.asyncio
async def test_agent_memory_semantic_has_indexes(db_engine):
    """agent_memory_semantic should have indexes on key columns."""
    async with db_engine.connect() as conn:
        def get_indexes(connection):
            inspector = inspect(connection)
            return inspector.get_indexes("agent_memory_semantic")

        indexes = await conn.run_sync(get_indexes)
        indexed_columns = set()
        for idx in indexes:
            indexed_columns.update(idx["column_names"])

        assert "agent_type" in indexed_columns
        assert "organization_id" in indexed_columns
        assert "fact_type" in indexed_columns
