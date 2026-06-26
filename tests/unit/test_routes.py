"""tests/unit/test_routes.py
Unit tests for API route handlers.
"""
import sys
import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from aiohttp import web
from core.api.routes import handle_status, handle_health, _redact_secrets
from core.api.hub_state import hub

class TestRouteHandlers:
    """Test HTTP API route handlers."""
    
    @pytest.mark.asyncio
    async def test_handle_status_returns_online(self):
        """Status endpoint should return online status."""
        request = MagicMock()
        
        # Mock hub components
        hub.rag = MagicMock()
        hub.rag.is_available.return_value = True
        hub.rag.get_memory_count.return_value = 42
        
        response = await handle_status(request)
        assert response.status == 200
        data = json.loads(response.text)
        assert data["status"] == "online"
        assert "metrics" in data
    
    @pytest.mark.asyncio
    async def test_handle_health_returns_healthy(self):
        """Health endpoint should return healthy status."""
        request = MagicMock()
        
        hub.config = MagicMock()
        hub.config.get.return_value = "ollama"
        hub.bridge = MagicMock()
        hub.vision = MagicMock()
        
        response = await handle_health(request)
        assert response.status == 200
        data = json.loads(response.text)
        assert data["status"] == "healthy"
        assert "bridges" in data
    
    def test_redact_secrets_masks_api_keys(self):
        """_redact_secrets should mask sensitive values."""
        data = {
            "API_KEY": "sk-1234567890abcdef",
            "normal_key": "visible_value",
            "DISCORD_TOKEN": "supersecret",
        }
        redacted = _redact_secrets(data)
        assert "***" in redacted["API_KEY"]
        assert redacted["normal_key"] == "visible_value"
        assert "***" in redacted["DISCORD_TOKEN"]
    
    def test_redact_secrets_preserves_structure(self):
        """_redact_secrets should preserve nested structure."""
        data = {
            "llm": {
                "API_KEY": "secret123",
                "url": "http://example.com"
            }
        }
        redacted = _redact_secrets(data)
        assert redacted["llm"]["url"] == "http://example.com"
        assert "***" in redacted["llm"]["API_KEY"]
