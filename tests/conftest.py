# tests/conftest.py
"""Pytest fixtures and configuration for Aiko test suite."""
import os
import sys
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch


@pytest.fixture(autouse=True)
def clean_env():
    """Clean environment variables before each test."""
    old_env = dict(os.environ)
    yield
    os.environ.clear()
    os.environ.update(old_env)

@pytest.fixture
def temp_dir():
    """Provide a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)

@pytest.fixture
def mock_config():
    """Provide a mock configuration object."""
    config = MagicMock()
    config.get_all.return_value = {
        "LLM_URL": "http://localhost:11434/api/chat",
        "LLM_MODEL": "gemma4:31b-cloud",
        "TTS_ENABLED": True,
        "TTS_VOICE": "vivian",
        "TTS_SPEED": 0.9,
    }
    config.get.side_effect = lambda key, default=None: {
        "LLM_URL": "http://localhost:11434/api/chat",
        "LLM_MODEL": "gemma4:31b-cloud",
        "TTS_ENABLED": True,
        "TTS_VOICE": "vivian",
        "TTS_SPEED": 0.9,
        "PROVIDER": "ollama",
    }.get(key, default)
    return config

@pytest.fixture
def mock_settings_file(temp_dir):
    """Create a mock user_settings.json file."""
    settings = {
        "llm": {"url": "http://localhost:11434/api/chat", "model": "gemma4:31b-cloud"},
        "tts": {"enabled": True, "voice": "vivian", "speed": 0.9},
    }
    path = temp_dir / "user_settings.json"
    path.write_text(json.dumps(settings), encoding="utf-8")
    return path
