import base64
import hashlib

from cryptography.fernet import Fernet

from clara.config import get_settings


def get_fernet() -> Fernet:
    """Return a Fernet instance keyed from ENCRYPTION_KEY (preferred) or SECRET_KEY."""
    settings = get_settings()
    secret = settings.encryption_key or settings.secret_key.get_secret_value()
    key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())
    return Fernet(key)
