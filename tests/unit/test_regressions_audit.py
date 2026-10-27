"""Focused regression tests for behaviours fixed during the QA/DX audit.

Deliberately small, fast and deterministic: no network, no live event-loop
servers, no sleeps. Each test pins one behaviour that previously regressed or
was entirely untested.
"""
import asyncio
import json

from core.api import broadcast
from core.api.auth import (
    _b64url, _unb64url, generate_token, verify_token,
    sign_private_resource, verify_private_resource,
)
from core.api.routes import (
    _sanitize_input, handle_mobile_pair_code, handle_mobile_pair_exchange,
)
from core.config_manager import encrypt_string, decrypt_string
from core.security import policy_engine


# --- (a) input sanitisation -------------------------------------------------
def test_sanitize_input_strips_control_chars_and_truncates():
    """NUL/control chars are removed, newlines kept, and 50_000 chars is the cap."""
    cleaned, is_safe, reason = _sanitize_input("hello\x00\x07world\nline2")
    assert is_safe is True
    assert reason == ""
    assert "\x00" not in cleaned
    assert "\x07" not in cleaned
    assert "\n" in cleaned, "newlines must be preserved"
    assert cleaned == "helloworld\nline2"

    # API contract max_length is 50_000; longer input must be truncated, not rejected.
    long_cleaned, long_safe, long_reason = _sanitize_input("a" * 60_000)
    assert long_safe is True
    assert long_reason == ""
    assert len(long_cleaned) == 50_000


# --- (b) token verification -------------------------------------------------
def test_verify_token_rejects_expired_and_tampered_payload():
    """Expiry is enforced, and a payload edited without re-signing is rejected."""
    assert policy_engine._secret, "policy_engine secret must be initialised"

    good = generate_token("tester", expires_hours=1)
    assert verify_token(good) is not None

    expired = generate_token("tester", expires_hours=-1)
    assert verify_token(expired) is None

    header, payload, signature = good.split(".")
    claims = json.loads(_unb64url(payload))
    claims["sub"] = "attacker"
    claims["is_admin"] = True
    forged_payload = _b64url(json.dumps(claims).encode())
    assert verify_token(f"{header}.{forged_payload}.{signature}") is None


def test_satellite_token_is_explicitly_non_admin():
    token = generate_token("satellite:discord", is_admin=False, token_type="satellite")
    claims = verify_token(token)
    assert claims["is_admin"] is False
    assert claims["token_type"] == "satellite"
    assert policy_engine.is_admin(claims["sub"], claims["is_admin"]) is False


def test_mobile_pair_code_is_one_use_and_issues_limited_token():
    class Request(dict):
        def __init__(self, *, user=None, payload=None):
            super().__init__(user=user or {})
            self.payload = payload or {}

        async def json(self):
            return self.payload

    async def exercise():
        response = await handle_mobile_pair_code(Request(user={"is_admin": True}))
        assert response.status == 200
        pairing = json.loads(response.text)
        code = pairing["pairing_code"]

        exchange = await handle_mobile_pair_exchange(Request(payload={"pairing_code": code}))
        assert exchange.status == 200
        claims = verify_token(json.loads(exchange.text)["token"])
        assert claims["is_admin"] is False
        assert claims["token_type"] == "mobile"
        assert claims["sub"].startswith("mobile:")

        replay = await handle_mobile_pair_exchange(Request(payload={"pairing_code": code}))
        assert replay.status == 401

        denied = await handle_mobile_pair_code(Request(user={"is_admin": False}))
        assert denied.status == 403

    asyncio.run(exercise())


def test_private_media_signature_is_short_lived_and_filename_bound():
    expires, signature = sign_private_resource("upload", "private_abc123.png")
    assert verify_private_resource("upload", "private_abc123.png", str(expires), signature)
    assert not verify_private_resource("tts", "private_abc123.png", str(expires), signature)
    assert not verify_private_resource("upload", "other.png", str(expires), signature)
    assert not verify_private_resource("upload", "../secret.txt", str(expires), signature)


def test_config_secret_encryption_round_trip():
    secret = "aiko-test-secret-do-not-persist"
    encrypted = encrypt_string(secret)
    assert encrypted.startswith(("dpapi:v2:", "fernet:v2:"))
    assert secret not in encrypted
    assert decrypt_string(encrypted) == secret


# --- (c) broadcast fan-out --------------------------------------------------
class _FakeWebSocket:
    """Minimal aiohttp WebSocketResponse stand-in."""

    def __init__(self, closed: bool = False):
        self.closed = closed
        self.sent: list[str] = []

    async def send_str(self, message: str) -> None:
        self.sent.append(message)


def test_broadcast_keeps_healthy_client_when_another_is_closed():
    """A closed peer must not cause a healthy peer to be dropped from ws_clients."""
    healthy = _FakeWebSocket()
    dead = _FakeWebSocket(closed=True)

    broadcast.ws_clients.clear()
    broadcast.webrtc_channels.clear()
    broadcast.ws_clients.update({healthy, dead})
    try:
        asyncio.run(broadcast.broadcast_event("audit_event", {"k": "v"}))

        assert healthy in broadcast.ws_clients, "healthy client was dropped"
        assert dead not in broadcast.ws_clients, "closed client was not reaped"
        assert len(healthy.sent) == 1
        envelope = json.loads(healthy.sent[0])
        assert envelope["type"] == "audit_event"
        assert envelope["payload"] == {"k": "v"}
    finally:
        broadcast.ws_clients.clear()
        broadcast.webrtc_channels.clear()
