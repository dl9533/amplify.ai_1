"""Pytest configuration for discovery tests."""
import sys
from pathlib import Path

# Add the discovery directory to the Python path
discovery_path = Path(__file__).parent.parent
sys.path.insert(0, str(discovery_path))
