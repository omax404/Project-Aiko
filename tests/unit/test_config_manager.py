"""tests/unit/test_config_manager.py
Unit tests for configuration management and URL normalization.
"""
import os
import sys
import json
import pytest
from pathlib import Path


from core.config_manager import ConfigManager, config, normalize_llm_url

class TestConfigManager:
    """Test configuration loading, saving, and basic operations."""

    def test_get_with_default(self):
        """get() should return default for missing keys."""
        result = config.get("NONEXISTENT_KEY", "default_value")
        assert result == "default_value"

    def test_set_and_get(self):
        """set() should store key-value pair and retrieve it."""
        config.set("TEST_SET_KEY", "test_val")
        assert config.get("TEST_SET_KEY") == "test_val"

    def test_update_bulk(self):
        """update() should bulk update keys."""
        config.update({"BULK_1": "val1", "BULK_2": "val2"})
        assert config.get("BULK_1") == "val1"
        assert config.get("BULK_2") == "val2"

    def test_get_all_returns_dict(self):
        """get_all() should return configuration dictionary."""
        all_config = config.get_all()
        assert isinstance(all_config, dict)
        assert all_config.get("BULK_1") == "val1"

    def test_normalize_llm_url(self):
        """Test URL normalization logic."""
        assert normalize_llm_url("") == ""
        assert normalize_llm_url("http://127.0.0.1:11434") == "http://127.0.0.1:11434"
        assert normalize_llm_url("https://api.openai.com/v1") == "https://api.openai.com/v1/chat/completions"
        assert normalize_llm_url("https://openrouter.ai/api/v1") == "https://openrouter.ai/api/v1/chat/completions"
