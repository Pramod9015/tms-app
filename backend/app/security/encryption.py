"""
AES-256 field encryption using Fernet (AES-128-CBC with HMAC-SHA256).
For true AES-256-GCM, see encrypt_aes256_gcm / decrypt_aes256_gcm below.
All encrypted values are stored as base64 strings.
"""
import os
import base64
import hashlib
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.config import settings

# ─── Fernet (default, recommended) ────────────────────────────────────────────

def _get_fernet() -> Fernet:
    key = settings.AES_ENCRYPTION_KEY
    if not key:
        # Auto-generate a one-time key (only safe for dev/testing)
        key = Fernet.generate_key().decode()
    if isinstance(key, str):
        key = key.encode()
    return Fernet(key)


def encrypt_field(value: str | None) -> str | None:
    """Encrypt a string field. Returns base64 ciphertext or None."""
    if value is None:
        return None
    f = _get_fernet()
    return f.encrypt(value.encode()).decode()


def decrypt_field(ciphertext: str | None) -> str | None:
    """Decrypt a previously encrypted field. Returns plaintext or None."""
    if ciphertext is None:
        return None
    try:
        f = _get_fernet()
        return f.decrypt(ciphertext.encode()).decode()
    except (InvalidToken, Exception):
        return ciphertext  # Return as-is if not encrypted (migration safety)


# ─── Raw AES-256-GCM (for bulk data / files) ──────────────────────────────────

def _derive_key_256(secret: str) -> bytes:
    """Derive a 32-byte key from settings secret using SHA-256."""
    return hashlib.sha256(secret.encode()).digest()


def encrypt_aes256_gcm(plaintext: str) -> str:
    """
    Encrypt using AES-256-GCM.
    Returns: base64(nonce + ciphertext)
    """
    key = _derive_key_256(settings.SECRET_KEY)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # 96-bit nonce
    ct = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return base64.urlsafe_b64encode(nonce + ct).decode()


def decrypt_aes256_gcm(token: str) -> str:
    """Decrypt AES-256-GCM ciphertext produced by encrypt_aes256_gcm."""
    key = _derive_key_256(settings.SECRET_KEY)
    aesgcm = AESGCM(key)
    raw = base64.urlsafe_b64decode(token.encode())
    nonce, ct = raw[:12], raw[12:]
    return aesgcm.decrypt(nonce, ct, None).decode()


def generate_fernet_key() -> str:
    """Utility: generate a new Fernet key to put in .env."""
    return Fernet.generate_key().decode()
