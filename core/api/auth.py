"""
core/api/auth.py
JWT Authentication for Aiko Neural Hub.
No external dependencies — uses hmac + json + base64.
"""
import hmac
import hashlib
import json
import base64
import time
import os
import logging
from aiohttp import web
from core.security import policy_engine

logger = logging.getLogger("Auth")

def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')

def _unb64url(data: str) -> bytes:
    padding = 4 - len(data) % 4
    if padding != 4:
        data += '=' * padding
    return base64.urlsafe_b64decode(data)

def generate_token(user_id: str, is_admin: bool = False, expires_hours: int = 168) -> str:
    """Generate a JWT token. Default expiry: 7 days."""
    secret = policy_engine._secret
    header = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = _b64url(json.dumps({
        "sub": user_id,
        "is_admin": bool(is_admin),
        "iat": time.time(),
        "exp": time.time() + expires_hours * 3600
    }).encode())
    sig_raw = hmac.new(secret.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest()
    sig = _b64url(sig_raw)
    return f"{header}.{payload}.{sig}"

def verify_token(token: str) -> dict:
    """Verify a JWT token and return payload or None."""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        payload = json.loads(_unb64url(parts[1]))
        if payload.get("exp", 0) < time.time():
            return None
        secret = policy_engine._secret
        
        # Verify standard base64url signature
        expected_raw = hmac.new(secret.encode(), f"{parts[0]}.{parts[1]}".encode(), hashlib.sha256).digest()
        expected_b64url = _b64url(expected_raw)
        
        # Also support legacy hex signature for backwards compatibility
        expected_hex = hmac.new(secret.encode(), f"{parts[0]}.{parts[1]}".encode(), hashlib.sha256).hexdigest()
        
        if not (hmac.compare_digest(parts[2], expected_b64url) or hmac.compare_digest(parts[2], expected_hex)):
            return None
        return payload
    except (json.JSONDecodeError, ValueError, TypeError, KeyError, IndexError) as e:
        logger.debug(f"Token verification failed: {e}")
        return None

# Public paths that don't require JWT middleware authentication
# Note: /token handles local loopback checking itself, and /ws enforces token validation during handshake.
PUBLIC_PATHS = {"/status", "/health", "/", "/token", "/ws"}

@web.middleware
async def jwt_middleware(request, handler):
    """Require JWT Bearer token on all /api/* routes."""
    path = request.path
    
    # Public paths bypass auth
    if path in PUBLIC_PATHS:
        return await handler(request)
    if path.startswith(("/assets/", "/uploads/", "/stickers/", "/api/tts/")):
        return await handler(request)
    # SECURITY: All /api/* routes require a valid Bearer token.
    # Subnet/loopback bypass has been removed.
    # All clients (local or remote) must present a valid Bearer token.
    # If deployed behind a reverse proxy the proxy IP would otherwise bypass auth.
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return web.json_response({"error": "Unauthorized — Bearer token required"}, status=401)
    
    token = auth[7:]
    payload = verify_token(token)
    if not payload:
        return web.json_response({"error": "Invalid or expired token"}, status=401)
    
    request["user"] = payload
    return await handler(request)
