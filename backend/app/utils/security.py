import base64
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import settings
from app.exceptions.base import ProviderException


def _get_kek() -> bytes:
    """Decodes and validates the base64 Key Encryption Key (KEK)."""
    try:
        return base64.b64decode(settings.ENCRYPTION_KEY)
    except Exception as e:
        raise ValueError("ENCRYPTION_KEY base64 format invalid.") from e


def encrypt_payload(plaintext: str) -> str:
    """
    Encrypts sensitive payloads (like credentials) using AES-256-GCM.
    Returns base64 encoded string containing IV (nonce) + Ciphertext.
    """
    try:
        # 1. Decode KEK (KMS equivalent key)
        kek = _get_kek()
        
        # 2. Generate random 12-byte initialization vector (nonce)
        nonce = os.urandom(12)
        
        # 3. Encrypt payload
        aesgcm = AESGCM(kek)
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        
        # 4. Pack IV and Ciphertext together
        packed = nonce + ciphertext
        return base64.b64encode(packed).decode("utf-8")
    except Exception as e:
        raise ProviderException(f"Encryption process failure: {str(e)}", status_code=500)


def decrypt_payload(ciphertext_b64: str) -> str:
    """
    Decrypts AES-256-GCM encrypted base64 payload.
    Reconstructs IV and ciphertext.
    """
    try:
        kek = _get_kek()
        packed = base64.b64decode(ciphertext_b64)
        
        # Split IV (first 12 bytes) and ciphertext
        nonce = packed[:12]
        ciphertext = packed[12:]
        
        aesgcm = AESGCM(kek)
        plaintext_bytes = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext_bytes.decode("utf-8")
    except Exception as e:
        raise ProviderException(f"Decryption process failure: {str(e)}", status_code=500)
