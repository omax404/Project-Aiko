import re
import hashlib
import time
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from core.structured_logger import system_logger

class SecurityManager:
    """
    Zero-Trust Security & Policy Enforcement
    """
    def __init__(self):
        # Stub secret for JWT/HMAC
        self._secret = "aiko_local_zero_trust_stub_r8w98q"

    def generate_auth_token(self, agent_id: str = "Aiko_Main") -> str:
        """
        Generate a short-lived HMAC token for OpenClaw API handshakes.
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
            
        admin_ids_raw = os.getenv("ADMIN_IDS", "")
        admin_ids = [uid.strip() for uid in admin_ids_raw.split(",") if uid.strip()]
        
        return user_id in admin_ids

    def validate_input(self, text: str) -> bool:
        """
        Basic Prompt Injection mitigation.
        Returns False if malicious intent is suspected.
        """
        forbidden_patterns = [
            r"ignore all previous instructions",
            r"system override",
            r"you are now a",
            r"forget your instructions"
        ]
        text_lower = text.lower()
        for pattern in forbidden_patterns:
            if re.search(pattern, text_lower):
                system_logger.warning(f"Intrusion Detected: Blocked potential injection -> {text[:50]}...")
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
    Advanced Symmetry AES Encryption for Local AI Memory.
    Generates a secure Fernet key derived from a master secret.
    """
    def __init__(self, master_secret: str = "Aiko_Elite_Vault_V2"):
        salt = b"aiko_salt_local_db_938"
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_secret.encode()))
        self.fernet = Fernet(key)

    def encrypt(self, data: str) -> bytes:
        return self.fernet.encrypt(data.encode('utf-8'))

    def decrypt(self, token: bytes) -> str:
        try:
            return self.fernet.decrypt(token).decode('utf-8')
        except Exception as e:
            system_logger.error(f"Memory Decryption Failed: {e}")
            raise

# Global Security Policy Engine & Cipher
policy_engine = SecurityManager()
memory_cipher = MemoryCipher()
