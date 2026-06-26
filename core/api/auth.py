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

def generate_token(user_id: str, expires_hours: int = 168) -> str:
    """Generate a JWT-like token. Default expiry: 7 days."""
    secret = policy_engine._secret
    header = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = _b64url(json.dumps({
        "sub": user_id,
        "iat": time.time(),
        "exp": time.time() + expires_hours * 3600
    }).encode())
    sig = hmac.new(secret.encode(), f"{header}.{payload}".encode(), hashlib.sha256).hexdigest()
    return f"{header}.{payload}.{sig}"

def verify_token(token: str) -> dict:
    """Verify a JWT-like token and return payload or None."""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        payload = json.loads(_unb64url(parts[1]))
        if payload.get("exp", 0) < time.time():
            return None
        secret = policy_engine._secret
        expected = hmac.new(secret.encode(), f"{parts[0]}.{parts[1]}".encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(parts[2], expected):
            return None
        return payload
    except (json.JSONDecodeError, ValueError, TypeError, KeyError, IndexError) as e:
        logger.debug(f"Token verification failed: {e}")
        return None

# Public paths that don't require authentication
PUBLIC_PATHS = {"/status", "/health", "/ws", "/"}

@web.middleware
async def jwt_middleware(request, handler):
    """Require JWT Bearer token on all /api/* routes."""
    path = request.path
    
    # Public paths bypass auth
    if path in PUBLIC_PATHS:
        return await handler(request)
    if path.startswith(("/assets/", "/uploads/", "/stickers/", "/api/tts/")):
        return await handler(request)
    if path.startswith("/api/settings") and request.method == "GET":
        return await handler(request)
    
    # Local intranet / loopback subnet bypass for seamless mobile synchronization
    peer_ip = request.remote or ""
    is_local = (
        peer_ip in ("127.0.0.1", "::1", "localhost") or
        peer_ip.startswith("192.168.") or
        peer_ip.startswith("10.") or
        peer_ip.startswith("172.16.") or
        peer_ip.startswith("172.17.") or
        peer_ip.startswith("172.18.") or
        peer_ip.startswith("172.19.") or
        peer_ip.startswith("172.20.") or
        peer_ip.startswith("172.21.") or
        peer_ip.startswith("172.22.") or
        peer_ip.startswith("172.23.") or
        peer_ip.startswith("172.24.") or
        peer_ip.startswith("172.25.") or
        peer_ip.startswith("172.26.") or
        peer_ip.startswith("172.27.") or
        peer_ip.startswith("172.28.") or
        peer_ip.startswith("172.29.") or
        peer_ip.startswith("172.30.") or
        peer_ip.startswith("172.31.")
    )
    
    if is_local:
        request["user"] = {"sub": "local_peer", "iat": time.time(), "exp": time.time() + 3600}
        return await handler(request)
    
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return web.json_response({"error": "Unauthorized — Bearer token required"}, status=401)
    
    token = auth[7:]
    payload = verify_token(token)
    if not payload:
        return web.json_response({"error": "Invalid or expired token"}, status=401)
    
    request["user"] = payload
    return await handler(request)
