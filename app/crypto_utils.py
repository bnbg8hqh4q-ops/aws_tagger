
import os
from cryptography.fernet import Fernet

KEY_FILE = os.path.join(os.path.dirname(__file__), 'data', 'fernet.key')

def _ensure_key():
    os.makedirs(os.path.dirname(KEY_FILE), exist_ok=True)
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, 'wb') as f:
            f.write(key)
    with open(KEY_FILE, 'rb') as f:
        key = f.read()
    return key

def get_cipher():
    key = _ensure_key()
    return Fernet(key)

def encrypt(text: str) -> str:
    from cryptography.fernet import InvalidToken
    cipher = get_cipher()
    return cipher.encrypt(text.encode()).decode()

def decrypt(token: str) -> str:
    cipher = get_cipher()
    return cipher.decrypt(token.encode()).decode()
