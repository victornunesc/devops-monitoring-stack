"""
Pytest configuration and shared fixtures for ViaIpe Collector tests
"""
import pytest
import sys
from pathlib import Path

src_path = Path(__file__).parent.parent / 'src'
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


@pytest.fixture(autouse=True)
def reset_environment(monkeypatch):
    """Reset environment variables before each test"""
    pass


@pytest.fixture
def mock_logger():
    """Mock logger to prevent log output during tests"""
    import logging
    from unittest.mock import MagicMock
    
    mock = MagicMock()
    return mock
