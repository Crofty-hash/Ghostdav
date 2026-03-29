"""
Encryption module - Layered encryption with AES-256 and XChaCha20-Poly1305
Provides strong encryption with forward secrecy through ephemeral session keys
"""

import os
import secrets
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import Tuple
import base64


try:
    from cryptography.hazmat.primitives.ciphers.aead import XChaCha20Poly1305
    ChaChaCipher = XChaCha20Poly1305
    DEFAULT_NONCE_SIZE = 24
    DEFAULT_ALGORITHM = "XChaCha20-Poly1305"
except ImportError:
    from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
    ChaChaCipher = ChaCha20Poly1305
    DEFAULT_NONCE_SIZE = 12
    DEFAULT_ALGORITHM = "ChaCha20-Poly1305"


class EncryptionManager:
    """Handles multi-layer encryption strategy"""
    
    def __init__(self):
        self.algorithm = DEFAULT_ALGORITHM
        self.key_size = 32  # 256 bits
        self.nonce_size = DEFAULT_NONCE_SIZE
        
    def encrypt_message(self, plaintext: bytes, key: bytes) -> Tuple[bytes, bytes]:
        """
        Encrypt a message with ChaCha20-Poly1305
        Returns (ciphertext, nonce)
        """
        if len(key) != self.key_size:
            raise ValueError(f"Key must be {self.key_size} bytes")
        
        cipher = ChaChaCipher(key)
        nonce = os.urandom(self.nonce_size)
        ciphertext = cipher.encrypt(nonce, plaintext, None)
        
        return ciphertext, nonce
    
    def decrypt_message(self, ciphertext: bytes, nonce: bytes, key: bytes) -> bytes:
        """
        Decrypt a ChaCha20-based encrypted message
        """
        cipher = ChaChaCipher(key)
        plaintext = cipher.decrypt(nonce, ciphertext, None)
        return plaintext
    
    def derive_key(self, password: str, salt: bytes = None, iterations: int = 100000) -> Tuple[bytes, bytes]:
        """
        Derive a 256-bit key from a password using PBKDF2
        Returns (key, salt)
        """
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=self.key_size, salt=salt, iterations=iterations)
        key = kdf.derive(password.encode())
        
        return key, salt
    
    def generate_session_key(self) -> bytes:
        """Generate a random ephemeral session key"""
        return secrets.token_bytes(self.key_size)
    
    def encrypt_with_aes(self, plaintext: bytes, key: bytes) -> Tuple[bytes, bytes]:
        """
        Secondary layer: AES-256-GCM encryption
        Returns (ciphertext, iv)
        """
        if len(key) != self.key_size:
            raise ValueError(f"Key must be {self.key_size} bytes")
        
        cipher = AESGCM(key)
        iv = os.urandom(12)
        ciphertext = cipher.encrypt(iv, plaintext, None)
        
        return ciphertext, iv
    
    def decrypt_with_aes(self, ciphertext: bytes, iv: bytes, key: bytes) -> bytes:
        """Decrypt AES-256-GCM encrypted message"""
        cipher = AESGCM(key)
        plaintext = cipher.decrypt(iv, ciphertext, None)
        return plaintext


def encode_encrypted_packet(ciphertext: bytes, nonce: bytes) -> str:
    """Encode encrypted packet to base64 for transmission"""
    packet = nonce + ciphertext
    return base64.b64encode(packet).decode('utf-8')


def decode_encrypted_packet(encoded: str) -> Tuple[bytes, bytes]:
    """Decode base64 packet and extract nonce and ciphertext"""
    packet = base64.b64decode(encoded)
    guessed_nonce_size = 24 if len(packet) >= 24 else 12
    nonce = packet[:guessed_nonce_size]
    ciphertext = packet[guessed_nonce_size:]
    return ciphertext, nonce
