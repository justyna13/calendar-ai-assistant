from cryptography.fernet import Fernet

from config.settings import settings

_fernet = Fernet(
    settings.token_encryption_key.get_secret_value().encode("utf-8")
)

def encrypt_token(token: str) -> str:
    encrypted = _fernet.encrypt(token.encode("utf-8"))
    return encrypted.decode("utf-8")

def decrypt_token(encrypted_token: str) -> str:
    decrypted = _fernet.decrypt(encrypted_token.encode("utf-8"))
    return decrypted.decode("utf-8")

