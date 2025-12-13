"""
Security module for handling encryption and decryption.
Uses the 'cryptography' library (Fernet/AES).
"""

from cryptography.fernet import Fernet

# In production, this key must come from ENV VARS and match strict length requirements
# Generate one via: verify_key = Fernet.generate_key()
# For now, we simulate a key generation if not provided (NOT FOR PRODUCTION PERSISTENCE)
_CIPHER_SUITE = None


def get_cipher_suite():
    """
    Get or create the Fernet cipher suite (Lazy Initialization).
    WARNING: Currently generates an ephemeral key. Data encrypted with this
    will be lost upon application restart unless a persistent key is configured.
    """
    global _CIPHER_SUITE  # pylint: disable=global-statement
    if _CIPHER_SUITE is None:
        # Ideally: key = settings.ENCRYPTION_KEY
        # For this example, ensuring we have a key
        key = Fernet.generate_key()
        _CIPHER_SUITE = Fernet(key)
    return _CIPHER_SUITE


def encrypt_data(data: bytes) -> bytes:
    """Encrypts bytes using AES (Fernet)."""
    return get_cipher_suite().encrypt(data)


def decrypt_data(data: bytes) -> bytes:
    """Decrypts bytes using AES (Fernet)."""
    return get_cipher_suite().decrypt(data)
