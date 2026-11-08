"""core/security/cipher.py
Advanced Symmetric AES Encryption for Local AI Memory.
"""
import os
import base64
from core.structured_logger import system_logger
from .manager import _get_secrets

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    _HAS_FERNET = True
except Exception:
    Fernet = None  # type: ignore[assignment]
    hashes = None  # type: ignore[assignment]
    PBKDF2HMAC = None  # type: ignore[assignment]
    _HAS_FERNET = False


class MemoryCipher:
    """
    Advanced Symmetric AES Encryption for Local AI Memory.
    Backward compatible: tries Fernet first, falls back to Windows DPAPI / config_manager when Rust DLLs are blocked.
    """
    def __init__(self):
        secrets_data = _get_secrets()
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
            self._salt = b"aiko_salt_local_db_938"

        self.fernet = None
        if _HAS_FERNET and PBKDF2HMAC and hashes and Fernet:
            try:
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=self._salt,
                    iterations=480000,
                )
                key = base64.urlsafe_b64encode(kdf.derive(self._master_secret.encode()))
                self.fernet = Fernet(key)
            except Exception:
                self.fernet = None

    def encrypt(self, data: str) -> bytes:
        if self.fernet is not None:
            return self.fernet.encrypt(data.encode('utf-8'))
        from core.config_manager import encrypt_string
        return encrypt_string(data).encode('utf-8')

    def decrypt(self, token: bytes) -> str:
        if self.fernet is not None:
            try:
                return self.fernet.decrypt(token).decode('utf-8')
            except Exception as e:
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
        from core.config_manager import decrypt_string
        raw = token.decode('utf-8', errors='replace') if isinstance(token, (bytes, bytearray)) else str(token)
        return decrypt_string(raw)

memory_cipher = MemoryCipher()
