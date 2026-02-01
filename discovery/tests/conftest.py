"""Pytest configuration for discovery tests."""
import sys
from pathlib import Path

import pytest

# Add the discovery directory to the Python path
discovery_path = Path(__file__).parent.parent
sys.path.insert(0, str(discovery_path))

# Configure pytest-asyncio
pytest_plugins = ("pytest_asyncio",)


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "integration: mark test as an integration test",
    )
