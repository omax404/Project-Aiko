# tests/test_api_security.py
import time
import pytest
from core.api.auth import generate_token, verify_token
from core.api.routes import _redact_secrets

def test_jwt_token_generation_and_verification():
    """Verify JWT token creation and valid signature parsing."""
    user_id = "test_user_42"
    token = generate_token(user_id, expires_hours=1)
    
    assert token is not None
    assert isinstance(token, str)
    assert len(token.split('.')) == 3
    
    payload = verify_token(token)
    assert payload is not None
    assert payload.get("sub") == user_id
    assert payload.get("exp") > time.time()

def test_expired_jwt_token_rejection():
    """Verify that an expired JWT token returns None."""
    user_id = "test_expired_user"
    token = generate_token(user_id, expires_hours=-1)  # Expired 1 hour ago
    
    payload = verify_token(token)
    assert payload is None

def test_tampered_jwt_token_rejection():
    """Verify that a tampered JWT payload fails HMAC validation."""
    user_id = "test_tamper_user"
    token = generate_token(user_id, expires_hours=1)
    parts = token.split('.')
    
    # Tamper with the signature
    fake_token = f"{parts[0]}.{parts[1]}.bad_signature_hash"
    payload = verify_token(fake_token)
    assert payload is None

def test_secrets_redaction():
    """Verify sensitive keys are masked before logging or API return."""
    raw_data = {
        "username": "aiko_user",
        "API_KEY": "sk-proj-1234567890abcdef",
        "nested": {
            "DISCORD_TOKEN": "bot_token_secret_value",
            "safe_val": "hello_world"
        }
    }
    
    redacted = _redact_secrets(raw_data)
    assert redacted["username"] == "aiko_user"
    assert redacted["API_KEY"].startswith("sk-p...")
    assert "1234567890" not in redacted["API_KEY"]
    assert redacted["nested"]["DISCORD_TOKEN"].startswith("bot_...")
    assert redacted["nested"]["safe_val"] == "hello_world"
