"""
Encryption service for API keys using AES-256
"""
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
import base64
import hashlib
from typing import Tuple

from app.config import settings


class EncryptionService:
    """Service for encrypting and decrypting API keys"""

    def __init__(self):
        # Generate a 32-byte key from the encryption key in settings
        self.key = hashlib.sha256(settings.encryption_key.encode()).digest()

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string using AES-256-CBC

        Args:
            plaintext: The string to encrypt

        Returns:
            Base64-encoded string containing IV + ciphertext
        """
        # Generate random IV
        iv = get_random_bytes(AES.block_size)

        # Create cipher
        cipher = AES.new(self.key, AES.MODE_CBC, iv)

        # Encrypt and pad
        ciphertext = cipher.encrypt(pad(plaintext.encode('utf-8'), AES.block_size))

        # Combine IV + ciphertext and encode as base64
        encrypted_data = iv + ciphertext
        return base64.b64encode(encrypted_data).decode('utf-8')

    def decrypt(self, encrypted_text: str) -> str:
        """
        Decrypt an encrypted string

        Args:
            encrypted_text: Base64-encoded string containing IV + ciphertext

        Returns:
            Decrypted plaintext string
        """
        # Decode from base64
        encrypted_data = base64.b64decode(encrypted_text)

        # Extract IV and ciphertext
        iv = encrypted_data[:AES.block_size]
        ciphertext = encrypted_data[AES.block_size:]

        # Create cipher and decrypt
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)

        return plaintext.decode('utf-8')

    def encrypt_api_keys(self, api_key: str, secret_key: str) -> Tuple[str, str]:
        """
        Encrypt both API key and secret key

        Args:
            api_key: Binance API key
            secret_key: Binance secret key

        Returns:
            Tuple of (encrypted_api_key, encrypted_secret_key)
        """
        return self.encrypt(api_key), self.encrypt(secret_key)

    def decrypt_api_keys(self, encrypted_api_key: str, encrypted_secret_key: str) -> Tuple[str, str]:
        """
        Decrypt both API key and secret key

        Args:
            encrypted_api_key: Encrypted Binance API key
            encrypted_secret_key: Encrypted Binance secret key

        Returns:
            Tuple of (api_key, secret_key)
        """
        return self.decrypt(encrypted_api_key), self.decrypt(encrypted_secret_key)


# Global instance
encryption_service = EncryptionService()
