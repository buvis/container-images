from __future__ import annotations

import base64
import hashlib
import uuid as uuid_mod
from datetime import UTC, datetime, timedelta
from typing import Any

import argon2
import bcrypt
import jwt

from clara.config import get_settings
from clara.crypto import get_fernet

_ph = argon2.PasswordHasher()


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    # Argon2 hashes start with $argon2
    if hashed.startswith("$argon2"):
        try:
            return _ph.verify(hashed, plain)
        except argon2.exceptions.VerifyMismatchError:
            return False
    # Legacy bcrypt fallback
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def needs_rehash(hashed: str) -> bool:
    """True if hash is legacy bcrypt and should be upgraded to argon2."""
    return not hashed.startswith("$argon2")


def create_access_token(
    subject: str, expires_delta: timedelta | None = None
) -> str:
    settings = get_settings()
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    return jwt.encode(
        {
            "sub": subject,
            "exp": expire,
            "type": "access",
            "jti": str(uuid_mod.uuid4()),
        },
        settings.secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(subject: str) -> str:
    settings = get_settings()
    expire = datetime.now(UTC) + timedelta(
        days=settings.refresh_token_expire_days
    )
    return jwt.encode(
        {"sub": subject, "exp": expire, "type": "refresh"},
        settings.secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def create_reset_token(user_id: str) -> str:
    settings = get_settings()
    expire = datetime.now(UTC) + timedelta(minutes=15)
    return jwt.encode(
        {"sub": user_id, "exp": expire, "type": "reset"},
        settings.secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def create_2fa_temp_token(user_id: str) -> str:
    settings = get_settings()
    expire = datetime.now(UTC) + timedelta(minutes=5)
    return jwt.encode(
        {"sub": user_id, "exp": expire, "type": "2fa_temp"},
        settings.secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def _decode_token(token: str, expected_type: str) -> dict[str, Any] | None:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.secret_key.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
        )
        if payload.get("type") != expected_type:
            return None
        return payload
    except jwt.PyJWTError:
        return None


def decode_access_token(token: str) -> dict[str, Any] | None:
    return _decode_token(token, "access")


def decode_refresh_token(token: str) -> dict[str, Any] | None:
    return _decode_token(token, "refresh")


def decode_reset_token(token: str) -> dict[str, Any] | None:
    return _decode_token(token, "reset")


def decode_2fa_temp_token(token: str) -> dict[str, Any] | None:
    return _decode_token(token, "2fa_temp")


def _derive_legacy_key() -> bytes:
    """SHA-256 of SECRET_KEY, used only for legacy XOR fallback."""
    settings = get_settings()
    return hashlib.sha256(
        settings.secret_key.get_secret_value().encode()
    ).digest()


def encrypt_totp_secret(secret: str) -> str:
    return get_fernet().encrypt(secret.encode()).decode()


def decrypt_totp_secret(token: str) -> str:
    # Try Fernet first, fall back to legacy XOR for migration
    try:
        return get_fernet().decrypt(token.encode()).decode()
    except Exception:
        key = _derive_legacy_key()
        data = base64.urlsafe_b64decode(token.encode())
        decrypted = bytes(
            byte ^ key[index % len(key)] for index, byte in enumerate(data)
        )
        return decrypted.decode()
