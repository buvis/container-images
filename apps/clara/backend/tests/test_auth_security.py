from clara.auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    encrypt_totp_secret,
    decrypt_totp_secret,
)


def test_password_hash_verify():
    h = hash_password("secret")
    assert verify_password("secret", h)
    assert not verify_password("wrong", h)


def test_jwt_roundtrip(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test")
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@localhost/db")
    from clara.config import Settings

    token = create_access_token("user-123")
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "user-123"


def test_jwt_invalid():
    assert decode_access_token("garbage") is None


def test_totp_fernet_roundtrip():
    """Encrypt/decrypt with Fernet produces valid result."""
    secret = "JBSWY3DPEHPK3PXP"
    encrypted = encrypt_totp_secret(secret)
    assert encrypted.startswith("gAAAAA")  # Fernet token prefix
    assert decrypt_totp_secret(encrypted) == secret


def test_totp_xor_fallback():
    """Old XOR-encrypted secrets still decrypt via fallback."""
    import base64
    from clara.auth.security import _derive_legacy_key

    secret = "JBSWY3DPEHPK3PXP"
    key = _derive_legacy_key()
    data = secret.encode()
    xor_encrypted = base64.urlsafe_b64encode(
        bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
    ).decode()
    assert decrypt_totp_secret(xor_encrypted) == secret
