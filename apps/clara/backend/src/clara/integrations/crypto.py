from clara.crypto import get_fernet


def encrypt_credential(plaintext: str) -> str:
    """Encrypt a credential string, return base64-encoded ciphertext."""
    result: str = get_fernet().encrypt(plaintext.encode()).decode()
    return result


def decrypt_credential(ciphertext: str) -> str:
    """Decrypt a base64-encoded ciphertext back to plaintext."""
    result: str = get_fernet().decrypt(ciphertext.encode()).decode()
    return result
