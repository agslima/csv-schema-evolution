from cryptography.fernet import Fernet
from app.core.config import settings

# In production, this key must come from ENV VARS and match strict length requirements
# Generate one via: verify_key = Fernet.generate_key()
# For now, we simulate a key generation if not provided (NOT FOR PRODUCTION PERSISTENCE)
_CIPHER_SUITE = None


def get_cipher_suite():
    global _CIPHER_SUITE
    if _CIPHER_SUITE is None:
        # Ideally: key = settings.ENCRYPTION_KEY
        # For this example, ensuring we have a key (Warning: ephemeral key means data loss on restart if not fixed)
        key = Fernet.generate_key()
        _CIPHER_SUITE = Fernet(key)
    return _CIPHER_SUITE


def encrypt_data(data: bytes) -> bytes:
    """Encrypts bytes using AES (Fernet)."""
    return get_cipher_suite().encrypt(data)


def decrypt_data(data: bytes) -> bytes:
    """Decrypts bytes using AES (Fernet)."""
    return get_cipher_suite().decrypt(data)
