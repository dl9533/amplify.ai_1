"""Unit tests for base model configuration."""
import pytest


def test_base_model_exists():
    """Test that Base model is importable."""
    from app.models.base import Base
    assert Base is not None


def test_base_has_metadata():
    """Test that Base has metadata for table generation."""
    from app.models.base import Base
    assert hasattr(Base, "metadata")


def test_async_session_maker_exists():
    """Test that async session maker is available."""
    from app.models.base import async_session_maker
    assert async_session_maker is not None
