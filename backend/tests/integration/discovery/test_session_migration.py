"""Integration tests for discovery session tables migration.

These tests verify that the discovery session tables are correctly created by the
migration script and that foreign key relationships are properly configured.
"""

import pytest
from sqlalchemy import inspect


# Table existence tests

@pytest.mark.asyncio
async def test_discovery_sessions_table_exists(db_engine):
    """discovery_sessions table should exist after migration."""
    async with db_engine.connect() as conn:
        def get_tables(connection):
            inspector = inspect(connection)
            return inspector.get_table_names()

        tables = await conn.run_sync(get_tables)
        assert "discovery_sessions" in tables


@pytest.mark.asyncio
async def test_discovery_uploads_table_exists(db_engine):
    """discovery_uploads table should exist after migration."""
    async with db_engine.connect() as conn:
        def get_tables(connection):
            inspector = inspect(connection)
            return inspector.get_table_names()

        tables = await conn.run_sync(get_tables)
        assert "discovery_uploads" in tables


@pytest.mark.asyncio
async def test_discovery_role_mappings_table_exists(db_engine):
    """discovery_role_mappings table should exist after migration."""
    async with db_engine.connect() as conn:
        def get_tables(connection):
            inspector = inspect(connection)
            return inspector.get_table_names()

        tables = await conn.run_sync(get_tables)
        assert "discovery_role_mappings" in tables


@pytest.mark.asyncio
async def test_discovery_activity_selections_table_exists(db_engine):
    """discovery_activity_selections table should exist after migration."""
    async with db_engine.connect() as conn:
        def get_tables(connection):
            inspector = inspect(connection)
            return inspector.get_table_names()

        tables = await conn.run_sync(get_tables)
        assert "discovery_activity_selections" in tables


@pytest.mark.asyncio
async def test_discovery_analysis_results_table_exists(db_engine):
    """discovery_analysis_results table should exist after migration."""
    async with db_engine.connect() as conn:
        def get_tables(connection):
            inspector = inspect(connection)
            return inspector.get_table_names()

        tables = await conn.run_sync(get_tables)
        assert "discovery_analysis_results" in tables


@pytest.mark.asyncio
async def test_agentification_candidates_table_exists(db_engine):
    """agentification_candidates table should exist after migration."""
    async with db_engine.connect() as conn:
        def get_tables(connection):
            inspector = inspect(connection)
            return inspector.get_table_names()

        tables = await conn.run_sync(get_tables)
        assert "agentification_candidates" in tables


# Foreign key tests

@pytest.mark.asyncio
async def test_uploads_session_foreign_key(db_engine):
    """discovery_uploads.session_id should reference discovery_sessions."""
    async with db_engine.connect() as conn:
        def get_fks(connection):
            inspector = inspect(connection)
            return inspector.get_foreign_keys("discovery_uploads")

        fks = await conn.run_sync(get_fks)
        session_fk = next(
            (fk for fk in fks if "session_id" in fk["constrained_columns"]), None
        )
        assert session_fk is not None
        assert session_fk["referred_table"] == "discovery_sessions"


@pytest.mark.asyncio
async def test_role_mappings_session_foreign_key(db_engine):
    """discovery_role_mappings.session_id should reference discovery_sessions."""
    async with db_engine.connect() as conn:
        def get_fks(connection):
            inspector = inspect(connection)
            return inspector.get_foreign_keys("discovery_role_mappings")

        fks = await conn.run_sync(get_fks)
        session_fk = next(
            (fk for fk in fks if "session_id" in fk["constrained_columns"]), None
        )
        assert session_fk is not None
        assert session_fk["referred_table"] == "discovery_sessions"


@pytest.mark.asyncio
async def test_role_mappings_onet_code_foreign_key(db_engine):
    """discovery_role_mappings.onet_code should reference onet_occupations."""
    async with db_engine.connect() as conn:
        def get_fks(connection):
            inspector = inspect(connection)
            return inspector.get_foreign_keys("discovery_role_mappings")

        fks = await conn.run_sync(get_fks)
        onet_fk = next(
            (fk for fk in fks if "onet_code" in fk["constrained_columns"]), None
        )
        assert onet_fk is not None
        assert onet_fk["referred_table"] == "onet_occupations"


@pytest.mark.asyncio
async def test_activity_selections_session_foreign_key(db_engine):
    """discovery_activity_selections.session_id should reference discovery_sessions."""
    async with db_engine.connect() as conn:
        def get_fks(connection):
            inspector = inspect(connection)
            return inspector.get_foreign_keys("discovery_activity_selections")

        fks = await conn.run_sync(get_fks)
        session_fk = next(
            (fk for fk in fks if "session_id" in fk["constrained_columns"]), None
        )
        assert session_fk is not None
        assert session_fk["referred_table"] == "discovery_sessions"


@pytest.mark.asyncio
async def test_activity_selections_role_mapping_foreign_key(db_engine):
    """discovery_activity_selections.role_mapping_id should reference discovery_role_mappings."""
    async with db_engine.connect() as conn:
        def get_fks(connection):
            inspector = inspect(connection)
            return inspector.get_foreign_keys("discovery_activity_selections")

        fks = await conn.run_sync(get_fks)
        role_fk = next(
            (fk for fk in fks if "role_mapping_id" in fk["constrained_columns"]), None
        )
        assert role_fk is not None
        assert role_fk["referred_table"] == "discovery_role_mappings"


@pytest.mark.asyncio
async def test_activity_selections_dwa_foreign_key(db_engine):
    """discovery_activity_selections.dwa_id should reference onet_dwas."""
    async with db_engine.connect() as conn:
        def get_fks(connection):
            inspector = inspect(connection)
            return inspector.get_foreign_keys("discovery_activity_selections")

        fks = await conn.run_sync(get_fks)
        dwa_fk = next(
            (fk for fk in fks if "dwa_id" in fk["constrained_columns"]), None
        )
        assert dwa_fk is not None
        assert dwa_fk["referred_table"] == "onet_dwas"


@pytest.mark.asyncio
async def test_analysis_results_session_foreign_key(db_engine):
    """discovery_analysis_results.session_id should reference discovery_sessions."""
    async with db_engine.connect() as conn:
        def get_fks(connection):
            inspector = inspect(connection)
            return inspector.get_foreign_keys("discovery_analysis_results")

        fks = await conn.run_sync(get_fks)
        session_fk = next(
            (fk for fk in fks if "session_id" in fk["constrained_columns"]), None
        )
        assert session_fk is not None
        assert session_fk["referred_table"] == "discovery_sessions"


@pytest.mark.asyncio
async def test_analysis_results_role_mapping_foreign_key(db_engine):
    """discovery_analysis_results.role_mapping_id should reference discovery_role_mappings."""
    async with db_engine.connect() as conn:
        def get_fks(connection):
            inspector = inspect(connection)
            return inspector.get_foreign_keys("discovery_analysis_results")

        fks = await conn.run_sync(get_fks)
        role_fk = next(
            (fk for fk in fks if "role_mapping_id" in fk["constrained_columns"]), None
        )
        assert role_fk is not None
        assert role_fk["referred_table"] == "discovery_role_mappings"


@pytest.mark.asyncio
async def test_candidates_session_foreign_key(db_engine):
    """agentification_candidates.session_id should reference discovery_sessions."""
    async with db_engine.connect() as conn:
        def get_fks(connection):
            inspector = inspect(connection)
            return inspector.get_foreign_keys("agentification_candidates")

        fks = await conn.run_sync(get_fks)
        session_fk = next(
            (fk for fk in fks if "session_id" in fk["constrained_columns"]), None
        )
        assert session_fk is not None
        assert session_fk["referred_table"] == "discovery_sessions"


@pytest.mark.asyncio
async def test_candidates_role_mapping_foreign_key(db_engine):
    """agentification_candidates.role_mapping_id should reference discovery_role_mappings."""
    async with db_engine.connect() as conn:
        def get_fks(connection):
            inspector = inspect(connection)
            return inspector.get_foreign_keys("agentification_candidates")

        fks = await conn.run_sync(get_fks)
        role_fk = next(
            (fk for fk in fks if "role_mapping_id" in fk["constrained_columns"]), None
        )
        assert role_fk is not None
        assert role_fk["referred_table"] == "discovery_role_mappings"


# Column tests

@pytest.mark.asyncio
async def test_discovery_sessions_columns(db_engine):
    """discovery_sessions should have required columns."""
    async with db_engine.connect() as conn:
        def get_columns(connection):
            inspector = inspect(connection)
            return {col["name"] for col in inspector.get_columns("discovery_sessions")}

        columns = await conn.run_sync(get_columns)
        expected_columns = {
            "id",
            "user_id",
            "organization_id",
            "status",
            "current_step",
            "created_at",
            "updated_at",
        }
        assert expected_columns.issubset(columns)


@pytest.mark.asyncio
async def test_discovery_uploads_columns(db_engine):
    """discovery_uploads should have required columns."""
    async with db_engine.connect() as conn:
        def get_columns(connection):
            inspector = inspect(connection)
            return {col["name"] for col in inspector.get_columns("discovery_uploads")}

        columns = await conn.run_sync(get_columns)
        expected_columns = {
            "id",
            "session_id",
            "file_name",
            "file_url",
            "row_count",
            "column_mappings",
            "detected_schema",
            "created_at",
            "updated_at",
        }
        assert expected_columns.issubset(columns)


@pytest.mark.asyncio
async def test_discovery_role_mappings_columns(db_engine):
    """discovery_role_mappings should have required columns."""
    async with db_engine.connect() as conn:
        def get_columns(connection):
            inspector = inspect(connection)
            return {col["name"] for col in inspector.get_columns("discovery_role_mappings")}

        columns = await conn.run_sync(get_columns)
        expected_columns = {
            "id",
            "session_id",
            "source_role",
            "onet_code",
            "confidence_score",
            "user_confirmed",
            "row_count",
            "created_at",
            "updated_at",
        }
        assert expected_columns.issubset(columns)


@pytest.mark.asyncio
async def test_discovery_activity_selections_columns(db_engine):
    """discovery_activity_selections should have required columns."""
    async with db_engine.connect() as conn:
        def get_columns(connection):
            inspector = inspect(connection)
            return {col["name"] for col in inspector.get_columns("discovery_activity_selections")}

        columns = await conn.run_sync(get_columns)
        expected_columns = {
            "id",
            "session_id",
            "role_mapping_id",
            "dwa_id",
            "selected",
            "user_modified",
            "created_at",
            "updated_at",
        }
        assert expected_columns.issubset(columns)


@pytest.mark.asyncio
async def test_discovery_analysis_results_columns(db_engine):
    """discovery_analysis_results should have required columns."""
    async with db_engine.connect() as conn:
        def get_columns(connection):
            inspector = inspect(connection)
            return {col["name"] for col in inspector.get_columns("discovery_analysis_results")}

        columns = await conn.run_sync(get_columns)
        expected_columns = {
            "id",
            "session_id",
            "role_mapping_id",
            "dimension",
            "dimension_value",
            "ai_exposure_score",
            "impact_score",
            "complexity_score",
            "priority_score",
            "breakdown",
            "created_at",
            "updated_at",
        }
        assert expected_columns.issubset(columns)


@pytest.mark.asyncio
async def test_agentification_candidates_columns(db_engine):
    """agentification_candidates should have required columns."""
    async with db_engine.connect() as conn:
        def get_columns(connection):
            inspector = inspect(connection)
            return {col["name"] for col in inspector.get_columns("agentification_candidates")}

        columns = await conn.run_sync(get_columns)
        expected_columns = {
            "id",
            "session_id",
            "role_mapping_id",
            "name",
            "description",
            "priority_tier",
            "estimated_impact",
            "selected_for_build",
            "intake_request_id",
            "created_at",
            "updated_at",
        }
        assert expected_columns.issubset(columns)
