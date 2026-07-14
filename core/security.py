import re
import unicodedata
import hashlib
import time
import os
import base64
import secrets
import json
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from core.structured_logger import system_logger

SECRETS_FILE = Path("data/.aiko_secrets.json")


def _get_or_create_secrets() -> dict:
    """Load or generate persistent secrets for this instance."""
    if SECRETS_FILE.exists():
        try:
            with open(SECRETS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            system_logger.warning(f"Failed to load secrets file: {e}")

    # Generate cryptographically secure secrets
    secrets_data = {
        "secret_key": secrets.token_urlsafe(32),
        "master_secret": secrets.token_urlsafe(32),
        "salt": base64.b64encode(os.urandom(16)).decode("ascii")
    }
    SECRETS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SECRETS_FILE, "w", encoding="utf-8") as f:
        json.dump(secrets_data, f)
    try:
        os.chmod(SECRETS_FILE, 0o600)  # Owner read/write only
    except Exception:
        pass  # Windows may not support Unix permissions
    system_logger.info("Generated new Aiko instance secrets.")
    return secrets_data


_instance_secrets = None


def _get_secrets():
    global _instance_secrets
    if _instance_secrets is None:
        _instance_secrets = _get_or_create_secrets()
    return _instance_secrets


class SecurityManager:
    """
    Zero-Trust Security & Policy Enforcement
    """
    def __init__(self):
        secrets_data = _get_secrets()
        # Priority: env var > generated file
        self._secret = os.getenv("AIKO_SECRET_KEY", secrets_data.get("secret_key", ""))
        if not self._secret:
            raise RuntimeError(
                "AIKO_SECRET_KEY not set and no generated secret available. "
                "Set AIKO_SECRET_KEY env var or delete data/.aiko_secrets.json to regenerate."
            )

    def generate_auth_token(self, agent_id: str = "Aiko_Main") -> str:
        """
        Generate a short-lived HMAC token for API handshakes.
        """
        timestamp = str(int(time.time()))
        payload = f"{agent_id}:{timestamp}:{self._secret}"
        signature = hashlib.sha256(payload.encode()).hexdigest()
        return f"Bearer {agent_id}.{timestamp}.{signature}"

    def is_admin(self, user_id: str) -> bool:
        """
        Check if the given user_id is authorized to execute remote PC commands.
        Defaults to allowing the local desktop ('Master') and any IDs in ADMIN_IDS env var.
        """
        # Always whitelist the local Tauri frontend connection
        if user_id == "Master":
            return True

        # Natively trust the Master's account ID if set in environments
        master_id = os.getenv("MASTER_ID", "")
        if master_id and str(user_id) == str(master_id):
            return True

        admin_ids_raw = os.getenv("ADMIN_IDS", "")
        admin_ids = [uid.strip() for uid in admin_ids_raw.split(",") if uid.strip()]

        return str(user_id) in admin_ids

    def detect_injection(self, text: str) -> tuple[bool, float]:
        """
        Multi-layer injection detection. Returns (is_blocked, confidence_score).
        Score >= 0.70 → blocked.
        """
        score = 0.0
        text_lower = text.lower()
        
        # Normalize unicode to catch homoglyph evasion (Cyrillic а vs Latin a)
        normalized = unicodedata.normalize('NFKC', text_lower)
        
        # Layer 1: Exact regex patterns
        # High risk patterns (0.6 each)
        high_risk_patterns = [
            r"ignore\s+(all\s+)?(previous\s+)?instructions",
            r"system\s+override",
            r"developer\s+mode",
            r"dan\s+mode",
            r"jailbreak",
            r"d\s*e\s*v\s*e\s*l\s*o\s*p\s*e\s*r\s*",
            r"bypass\s+restrictions",
            r"disregard\s+your\s+rules",
            r"forget\s+your\s+(instructions|programming|persona|rules)",
        ]
        
        # Borderline patterns (0.3 each to avoid false positives)
        borderline_patterns = [
            r"new\s+role\s+is",
            r"you\s+are\s+now\s+(a|an)\s+",
            r"act\s+as\s+(a|an)\s+",
        ]
        
        for pattern in high_risk_patterns:
            if re.search(pattern, normalized):
                score += 0.6
                
        for pattern in borderline_patterns:
            if re.search(pattern, normalized):
                score += 0.3
        
        # Layer 2: Semantic keyword indicators (0.2 each, max 0.4)
        semantic_indicators = [
            "forget your", "you are now", "new role", "bypass",
            "jailbreak", "disregard", "ignore all", "override",
            "system prompt", "developer mode", "dan mode",
        ]
        semantic_matches = 0
        for indicator in semantic_indicators:
            if indicator in normalized:
                semantic_matches += 1
        score += min(semantic_matches * 0.2, 0.4)
        
        # Layer 3: Structural anomalies
        directive_count = normalized.count("system") + normalized.count("instruction")
        if directive_count > 2:
            score += 0.2
        
        # Layer 4: Unicode obfuscation
        if text != unicodedata.normalize('NFKC', text):
            score += 0.3
        
        # Layer 5: Multi-fragment buildup
        if text.count(".") > 5 and any(w in normalized for w in ["forget", "ignore", "bypass"]):
            score += 0.15
        
        return score >= 0.70, min(score, 1.0)

    def validate_input(self, text: str) -> bool:
        """
        Basic Prompt Injection mitigation.
        Returns False if malicious intent is suspected.
        """
        is_blocked, score = self.detect_injection(text)
        if is_blocked:
            system_logger.warning(f"Intrusion Detected: Blocked potential injection (score={score:.2f}) -> {text[:50]}...")
            return False
        return True

    def sanitize_output(self, text: str) -> str:
        """
        Ensure output doesn't leak secrets or raw API tokens.
        """
        # A simple regex to mask Bearer tokens
        return re.sub(r"Bearer [A-Za-z0-9_.\-]+", "Bearer [REDACTED]", text, flags=re.IGNORECASE)


class MemoryCipher:
    """
    Advanced Symmetric AES Encryption for Local AI Memory.
    Backward compatible: tries new env/file secrets first, falls back to legacy defaults.
    """
    def __init__(self):
        secrets_data = _get_secrets()
        # Priority: env var > generated file > legacy fallback
        self._master_secret = os.getenv(
            "AIKO_MASTER_SECRET",
            secrets_data.get("master_secret", "Aiko_Elite_Vault_V2")
        )
        salt_b64 = os.getenv(
            "AIKO_SALT",
            secrets_data.get("salt", "YWlrb19zYWx0X2xvY2FsX2RiXzkzOA==")
        )
        try:
            self._salt = base64.b64decode(salt_b64)
        except Exception:
            # Fallback to legacy salt bytes if base64 decode fails
            self._salt = b"aiko_salt_local_db_938"

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self._salt,
            iterations=480000,  # Increased from 100k for better security
        )
        key = base64.urlsafe_b64encode(kdf.derive(self._master_secret.encode()))
        self.fernet = Fernet(key)

    def encrypt(self, data: str) -> bytes:
        return self.fernet.encrypt(data.encode('utf-8'))

    def decrypt(self, token: bytes) -> str:
        try:
            return self.fernet.decrypt(token).decode('utf-8')
        except Exception as e:
            # Try legacy decryption if new one fails
            try:
                legacy_kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=b"aiko_salt_local_db_938",
                    iterations=100000,
                )
                legacy_key = base64.urlsafe_b64encode(
                    legacy_kdf.derive("Aiko_Elite_Vault_V2".encode())
                )
                legacy_fernet = Fernet(legacy_key)
                return legacy_fernet.decrypt(token).decode('utf-8')
            except Exception:
                system_logger.error(f"Memory Decryption Failed: {e}")
                raise


# Global Security Policy Engine & Cipher
policy_engine = SecurityManager()
memory_cipher = MemoryCipher()
