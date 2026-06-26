"""tests/unit/test_auth.py
Unit tests for JWT authentication module.
"""
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.api.auth import generate_token, verify_token, jwt_middleware, PUBLIC_PATHS

class TestJWTAuth:
    """Test JWT token generation and verification."""
    
    def test_generate_token_structure(self):
        """Token should have header.payload.signature format."""
        token = generate_token("user123", expires_hours=1)
        parts = token.split(".")
        assert len(parts) == 3
    
    def test_verify_valid_token(self):
        """Valid token should return payload with user ID."""
        token = generate_token("user123", expires_hours=1)
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "user123"
        assert "exp" in payload
        assert "iat" in payload
    
    def test_verify_expired_token(self):
        """Expired token should return None."""
        token = generate_token("user123", expires_hours=-1)
        payload = verify_token(token)
        assert payload is None
    
    def test_verify_tampered_token(self):
        """Tampered token should return None."""
        token = generate_token("user123", expires_hours=1)
        tampered = token[:-5] + "XXXXX"
        payload = verify_token(tampered)
        assert payload is None
    
    def test_verify_malformed_token(self):
        """Malformed token should return None."""
        assert verify_token("not.a.token") is None
        assert verify_token("invalid") is None
        assert verify_token("") is None
    
    def test_public_paths_bypass_auth(self):
        """Public paths should not require authentication."""
        assert "/status" in PUBLIC_PATHS
        assert "/health" in PUBLIC_PATHS
        assert "/ws" in PUBLIC_PATHS
    
    @pytest.mark.asyncio
    async def test_jwt_middleware_allows_public(self):
        """Middleware should allow public paths without auth."""
        from aiohttp import web
        
        async def handler(request):
            return web.json_response({"ok": True})
        
        # Create a mock request for a public path
        request = MagicMock()
        request.path = "/status"
        request.headers = {}
        
        # This should pass through without auth
        response = await jwt_middleware(request, handler)
        assert response.status == 200
    
    @pytest.mark.asyncio
    async def test_jwt_middleware_rejects_no_auth(self):
        """Middleware should reject API calls without Bearer token."""
        from aiohttp import web
        from unittest.mock import MagicMock
        
        async def handler(request):
            return web.json_response({"ok": True})
        
        request = MagicMock()
        request.path = "/api/chat"
        request.remote = "198.51.100.1"
        request.headers = {}
        
        response = await jwt_middleware(request, handler)
        assert response.status == 401
        assert "Unauthorized" in response.text
