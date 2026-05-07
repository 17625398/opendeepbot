"""Pytest configuration for DeepTutor tests."""

import pytest
import os
import tempfile
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return {
        "llm": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "api_key": "test-key",
        },
        "channels": {
            "telegram": {
                "enabled": False,
                "token": "test-token",
            },
        },
    }


@pytest.fixture
def mock_env(monkeypatch):
    """Mock environment variables."""
    env_vars = {
        "LLM_PROVIDER": "deepseek",
        "LLM_API_KEY": "test-api-key",
        "TELEGRAM_ENABLED": "false",
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
