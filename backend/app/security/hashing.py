"""
Password hashing using bcrypt directly (compatible with bcrypt 5.x / Python 3.14).
Pre-hashes with SHA-256 to safely handle passwords longer than bcrypt's 72-byte limit.
"""
import hashlib
import base64
import bcrypt


def _prepare(password: str) -> bytes:
    """SHA-256 pre-hash → base64 → pass to bcrypt (avoids 72-byte truncation)."""
    digest = hashlib.sha256(password.encode()).digest()
    return base64.b64encode(digest)


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt (rounds=12)."""
    hashed = bcrypt.hashpw(_prepare(password), bcrypt.gensalt(rounds=12))
    return hashed.decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    return bcrypt.checkpw(_prepare(plain_password), hashed_password.encode())
