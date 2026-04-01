import sys
from pathlib import Path
import pytest

# Add src/ to sys.path so that bare module imports in market_server.py work
# when tests import via `from src.market_server import app`
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent.parent))


def pytest_configure(config):
    config.addinivalue_line("markers", "integration: marks tests as integration tests (deselect with '-m \"not integration\"')")
