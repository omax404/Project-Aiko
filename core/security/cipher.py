"""core/security/cipher.py
Advanced Symmetric AES Encryption for Local AI Memory.
"""
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from core.structured_logger import system_logger
from .manager import _get_secrets

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
            iterations=480000,
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

memory_cipher = MemoryCipher()
