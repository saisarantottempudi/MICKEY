"""
Fernet encryption for sensitive fields.
Key auto-generated on first use, stored in data/encryption.key.
Used for: calendar data, personal notes, any sensitive content.
"""

import os
from cryptography.fernet import Fernet
from config import DATA_DIR

KEY_FILE = os.path.join(DATA_DIR, "encryption.key")
_fernet = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is not None:
        return _fernet

    os.makedirs(os.path.dirname(KEY_FILE), exist_ok=True)

    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as f:
            key = f.read().strip()
    else:
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
        os.chmod(KEY_FILE, 0o600)

    _fernet = Fernet(key)
    return _fernet


def encrypt(plaintext: str) -> str:
    """Encrypt a string, return base64-encoded ciphertext."""
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    """Decrypt base64-encoded ciphertext, return plaintext."""
    return _get_fernet().decrypt(ciphertext.encode()).decode()


def is_encrypted(text: str) -> bool:
    """Check if text looks like Fernet-encrypted data."""
    try:
        # Fernet tokens are base64 and start with 'gAAAAA'
        return text.startswith("gAAAAA") and len(text) > 50
    except Exception:
        return False
