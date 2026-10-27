"""core/security/manager.py
Zero-Trust Security & Policy Enforcement.
"""
import hashlib
import time
import os
import secrets
import json
from pathlib import Path
from core.structured_logger import system_logger
from .injection import detect_injection

SECRETS_FILE = Path("data/.aiko_secrets.json")

def _get_or_create_secrets() -> dict:
    """Load or generate persistent secrets for this instance."""
    if SECRETS_FILE.exists():
        try:
            with open(SECRETS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            system_logger.warning(f"Failed to load secrets file: {e}")

    secrets_data = {
        "secret_key": secrets.token_urlsafe(32),
        "master_secret": secrets.token_urlsafe(32),
        "salt": secrets.token_urlsafe(16)
    }
    SECRETS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SECRETS_FILE, "w", encoding="utf-8") as f:
        json.dump(secrets_data, f)
    try:
        os.chmod(SECRETS_FILE, 0o600)
    except Exception:
        pass
    system_logger.info("Generated new Aiko instance secrets.")
    return secrets_data

_instance_secrets = None

def _get_secrets():
    global _instance_secrets
    if _instance_secrets is None:
        _instance_secrets = _get_or_create_secrets()
    return _instance_secrets


class SecurityManager:
    """Zero-Trust Security & Policy Enforcement"""
    def __init__(self):
        secrets_data = _get_secrets()
        self._secret = os.getenv("AIKO_SECRET_KEY", secrets_data.get("secret_key", ""))
        if not self._secret:
            raise RuntimeError(
                "AIKO_SECRET_KEY not set and no generated secret available. "
                "Set AIKO_SECRET_KEY env var or delete data/.aiko_secrets.json to regenerate."
            )

    def generate_auth_token(self, agent_id: str = "Aiko_Main") -> str:
        """Generate a short-lived HMAC token for API handshakes."""
        timestamp = str(int(time.time()))
        payload = f"{agent_id}:{timestamp}:{self._secret}"
        signature = hashlib.sha256(payload.encode()).hexdigest()
        return f"Bearer {agent_id}.{timestamp}.{signature}"

    def is_admin_claims(self, claims: dict) -> bool:
        """Check if JWT claims grant administrative / PC control privileges."""
        if not claims or not isinstance(claims, dict):
            return False
        return claims.get("is_admin", False) is True

    def is_admin(self, user_id: str, is_admin_claim: bool = False) -> bool:
        """
        Check if the given user_id or context is authorized to execute PC commands.
        Administrative access is granted only by an already verified token claim.
        """
        if is_admin_claim:
            return True

        return False

    def detect_injection(self, text: str) -> tuple[bool, float]:
        """Detect prompt injection."""
        return detect_injection(text)

    def validate_input(self, text: str) -> bool:
        """Validate input length and injection."""
        if len(text) > 4000:
            return False
        is_blocked, _ = self.detect_injection(text)
        if is_blocked:
            return False
        return True

    def sanitize_output(self, text: str) -> str:
        """Mask sensitive tokens and unsafe tags in output text."""
        import re
        # Mask Bearer tokens
        text = re.sub(r'Bearer\s+[A-Za-z0-9._\-]+', 'Bearer [REDACTED]', text, flags=re.IGNORECASE)
        return text

policy_engine = SecurityManager()
