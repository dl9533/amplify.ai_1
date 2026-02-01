# backend/tests/unit/modules/discovery/test_activity_repository.py
"""Unit tests for GWA/IWA/DWA work activity repositories."""

import pytest
from unittest.mock import MagicMock

from app.modules.discovery.repositories.onet_repository import (
    OnetGwaRepository,
    OnetIwaRepository,
    OnetDwaRepository,
)
from app.modules.discovery.models.onet import OnetGwa, OnetIwa, OnetDwa


@pytest.mark.asyncio
async def test_get_gwa_with_exposure_score(mock_db_session):
    """Should retrieve GWA with AI exposure score."""
    repo = OnetGwaRepository(mock_db_session)

    # Create mock GWA with exposure score
    mock_gwa = OnetGwa(
        id="4.A.1.a.1",
        name="Getting Information",
        description="Observing, receiving, and obtaining information",
        ai_exposure_score=0.75,
    )

    # Configure mock to return GWA
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = mock_gwa

    gwa = await repo.get_by_id("4.A.1.a.1")
    assert gwa is not None
    assert gwa.ai_exposure_score >= 0.0
    assert gwa.ai_exposure_score <= 1.0


@pytest.mark.asyncio
async def test_get_gwa_not_found(mock_db_session):
    """Should return None when GWA not found."""
    repo = OnetGwaRepository(mock_db_session)

    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = None

    gwa = await repo.get_by_id("nonexistent")
    assert gwa is None


@pytest.mark.asyncio
async def test_get_iwas_for_gwa(mock_db_session):
    """Should retrieve IWAs for a given GWA."""
    iwa_repo = OnetIwaRepository(mock_db_session)

    # Create mock IWAs
    mock_iwa1 = OnetIwa(
        id="4.A.1.a.1.I01",
        gwa_id="4.A.1.a.1",
        name="Communicating with supervisors",
        description="Communicating with supervisors, peers, or subordinates",
    )
    mock_iwa2 = OnetIwa(
        id="4.A.1.a.1.I02",
        gwa_id="4.A.1.a.1",
        name="Gathering information",
        description="Gathering information from various sources",
    )

    # Configure mock to return IWAs
    mock_result = mock_db_session.execute.return_value
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [mock_iwa1, mock_iwa2]
    mock_result.scalars.return_value = mock_scalars

    iwas = await iwa_repo.get_by_gwa_id("4.A.1.a.1")
    assert isinstance(iwas, list)
    assert len(iwas) == 2


@pytest.mark.asyncio
async def test_get_iwas_for_gwa_empty(mock_db_session):
    """Should return empty list when no IWAs found for GWA."""
    iwa_repo = OnetIwaRepository(mock_db_session)

    mock_result = mock_db_session.execute.return_value
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars

    iwas = await iwa_repo.get_by_gwa_id("nonexistent")
    assert isinstance(iwas, list)
    assert len(iwas) == 0


@pytest.mark.asyncio
async def test_get_dwas_for_iwa(mock_db_session):
    """Should retrieve DWAs for a given IWA."""
    dwa_repo = OnetDwaRepository(mock_db_session)

    # Create mock DWAs
    mock_dwa1 = OnetDwa(
        id="4.A.1.a.1.I01.D01",
        iwa_id="4.A.1.a.1.I01",
        name="Reviewing documents",
        description="Reviewing documents for accuracy",
    )

    mock_result = mock_db_session.execute.return_value
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [mock_dwa1]
    mock_result.scalars.return_value = mock_scalars

    dwas = await dwa_repo.get_by_iwa_id("4.A.1.a.1.I01")
    assert isinstance(dwas, list)
    assert len(dwas) == 1


@pytest.mark.asyncio
async def test_get_dwa_by_id(mock_db_session):
    """Should retrieve DWA by ID."""
    dwa_repo = OnetDwaRepository(mock_db_session)

    mock_dwa = OnetDwa(
        id="some_dwa_id",
        iwa_id="some_iwa_id",
        name="Test DWA",
        description="Test description",
        ai_exposure_override=None,
    )

    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = mock_dwa

    dwa = await dwa_repo.get_by_id("some_dwa_id")
    assert dwa is not None
    assert dwa.id == "some_dwa_id"


@pytest.mark.asyncio
async def test_dwa_inherits_gwa_score(mock_db_session):
    """DWA without override should inherit GWA exposure score."""
    dwa_repo = OnetDwaRepository(mock_db_session)

    # Create mock DWA without override
    mock_dwa = OnetDwa(
        id="some_dwa_id",
        iwa_id="some_iwa_id",
        name="Test DWA",
        description="Test description",
        ai_exposure_override=None,
    )

    # Create mock IWA
    mock_iwa = OnetIwa(
        id="some_iwa_id",
        gwa_id="some_gwa_id",
        name="Test IWA",
        description="Test IWA description",
    )

    # Create mock GWA with exposure score
    mock_gwa = OnetGwa(
        id="some_gwa_id",
        name="Test GWA",
        description="Test GWA description",
        ai_exposure_score=0.65,
    )

    # Set up relationships
    mock_iwa.gwa = mock_gwa
    mock_dwa.iwa = mock_iwa

    # Configure mock to return DWA (for first get_by_id call)
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = mock_dwa

    dwa = await dwa_repo.get_by_id("some_dwa_id")
    if dwa and dwa.ai_exposure_override is None:
        # Should be able to get inherited score
        effective_score = await dwa_repo.get_effective_exposure_score(dwa.id)
        assert effective_score is not None
        assert effective_score == 0.65


@pytest.mark.asyncio
async def test_dwa_uses_override_score(mock_db_session):
    """DWA with override should use its own score."""
    dwa_repo = OnetDwaRepository(mock_db_session)

    # Create mock DWA with override
    mock_dwa = OnetDwa(
        id="override_dwa_id",
        iwa_id="some_iwa_id",
        name="Override DWA",
        description="DWA with override",
        ai_exposure_override=0.85,
    )

    # Create mock IWA and GWA
    mock_iwa = OnetIwa(
        id="some_iwa_id",
        gwa_id="some_gwa_id",
        name="Test IWA",
        description="Test IWA description",
    )
    mock_gwa = OnetGwa(
        id="some_gwa_id",
        name="Test GWA",
        description="Test GWA description",
        ai_exposure_score=0.50,
    )

    mock_iwa.gwa = mock_gwa
    mock_dwa.iwa = mock_iwa

    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = mock_dwa

    effective_score = await dwa_repo.get_effective_exposure_score("override_dwa_id")
    assert effective_score == 0.85


@pytest.mark.asyncio
async def test_get_dwas_for_occupation(mock_db_session):
    """Should retrieve all DWAs associated with an occupation."""
    dwa_repo = OnetDwaRepository(mock_db_session)

    # Configure mock to return empty list (no association table yet)
    mock_result = mock_db_session.execute.return_value
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars

    dwas = await dwa_repo.get_by_occupation_code("15-1252.00")
    assert isinstance(dwas, list)


@pytest.mark.asyncio
async def test_iwa_get_by_id(mock_db_session):
    """Should retrieve IWA by ID."""
    iwa_repo = OnetIwaRepository(mock_db_session)

    mock_iwa = OnetIwa(
        id="test_iwa_id",
        gwa_id="test_gwa_id",
        name="Test IWA",
        description="Test description",
    )

    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = mock_iwa

    iwa = await iwa_repo.get_by_id("test_iwa_id")
    assert iwa is not None
    assert iwa.id == "test_iwa_id"


@pytest.mark.asyncio
async def test_gwa_list_all(mock_db_session):
    """Should list all GWAs."""
    repo = OnetGwaRepository(mock_db_session)

    mock_gwa1 = OnetGwa(id="4.A.1.a.1", name="GWA 1", ai_exposure_score=0.5)
    mock_gwa2 = OnetGwa(id="4.A.1.a.2", name="GWA 2", ai_exposure_score=0.7)

    mock_result = mock_db_session.execute.return_value
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [mock_gwa1, mock_gwa2]
    mock_result.scalars.return_value = mock_scalars

    gwas = await repo.list_all()
    assert len(gwas) == 2


@pytest.mark.asyncio
async def test_effective_score_returns_none_for_missing_dwa(mock_db_session):
    """Should return None when DWA not found."""
    dwa_repo = OnetDwaRepository(mock_db_session)

    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = None

    effective_score = await dwa_repo.get_effective_exposure_score("nonexistent")
    assert effective_score is None
