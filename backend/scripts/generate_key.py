# scripts/generate_key.py
from cryptography.fernet import Fernet


def generate_secret_key():
    """Generates a valid Fernet key for encryption."""
    key = Fernet.generate_key()
    print("\n--- COPY THIS KEY TO YOUR .env FILE ---")
    print(f"ENCRYPTION_KEY={key.decode()}")
    print("---------------------------------------\n")


if __name__ == "__main__":
    generate_secret_key()
