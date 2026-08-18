"""Hashing de contraseñas (PBKDF2-HMAC-SHA256) sin dependencias externas."""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets

_ALGO = "pbkdf2_sha256"
_ITERATIONS = 260_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERATIONS)
    return f"{_ALGO}${_ITERATIONS}${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def is_hashed(value: str) -> bool:
    return isinstance(value, str) and value.startswith(f"{_ALGO}$")


def verify_password(password: str, stored: str) -> bool:
    if not is_hashed(stored):
        return False
    try:
        _, iterations_s, salt_b64, digest_b64 = stored.split("$", 3)
        iterations = int(iterations_s)
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(digest_b64)
    except (ValueError, TypeError):
        return False
    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(actual, expected)
