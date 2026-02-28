"""Data encryption utilities using AES-256"""
import base64
import os
from typing import Optional
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from app.config import get_settings

settings = get_settings()


class EncryptionService:
    """Service for encrypting and decrypting sensitive data"""
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize encryption service
        
        Args:
            encryption_key: Base64-encoded 256-bit encryption key
        """
        key_str = encryption_key or settings.encryption_key
        
        if not key_str:
            raise ValueError("Encryption key not configured. Set ENCRYPTION_KEY in environment.")
        
        try:
            # Decode base64 key
            self.key = base64.b64decode(key_str)
            
            # Verify key length (must be 32 bytes for AES-256)
            if len(self.key) != 32:
                raise ValueError(f"Invalid key length: {len(self.key)} bytes. Expected 32 bytes for AES-256.")
        except Exception as e:
            raise ValueError(f"Invalid encryption key format: {e}")
        
        self.backend = default_backend()
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext using AES-256-CBC
        
        Args:
            plaintext: Text to encrypt
            
        Returns:
            Base64-encoded encrypted data (IV + ciphertext)
        """
        if not plaintext:
            return ""
        
        # Generate random IV (16 bytes for AES)
        iv = os.urandom(16)
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.CBC(iv),
            backend=self.backend
        )
        encryptor = cipher.encryptor()
        
        # Pad plaintext to block size (128 bits = 16 bytes)
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(plaintext.encode('utf-8')) + padder.finalize()
        
        # Encrypt
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        
        # Combine IV and ciphertext, then base64 encode
        encrypted_data = iv + ciphertext
        return base64.b64encode(encrypted_data).decode('utf-8')
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt data encrypted with encrypt()
        
        Args:
            encrypted_data: Base64-encoded encrypted data
            
        Returns:
            Decrypted plaintext
        """
        if not encrypted_data:
            return ""
        
        try:
            # Decode base64
            data = base64.b64decode(encrypted_data)
            
            # Extract IV (first 16 bytes) and ciphertext
            iv = data[:16]
            ciphertext = data[16:]
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(self.key),
                modes.CBC(iv),
                backend=self.backend
            )
            decryptor = cipher.decryptor()
            
            # Decrypt
            padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            
            # Unpad
            unpadder = padding.PKCS7(128).unpadder()
            plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
            
            return plaintext.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Decryption failed: {e}")
    
    def encrypt_dict(self, data: dict, fields_to_encrypt: list[str]) -> dict:
        """
        Encrypt specific fields in a dictionary
        
        Args:
            data: Dictionary containing data
            fields_to_encrypt: List of field names to encrypt
            
        Returns:
            Dictionary with specified fields encrypted
        """
        encrypted_data = data.copy()
        
        for field in fields_to_encrypt:
            if field in encrypted_data and encrypted_data[field]:
                encrypted_data[field] = self.encrypt(str(encrypted_data[field]))
        
        return encrypted_data
    
    def decrypt_dict(self, data: dict, fields_to_decrypt: list[str]) -> dict:
        """
        Decrypt specific fields in a dictionary
        
        Args:
            data: Dictionary containing encrypted data
            fields_to_decrypt: List of field names to decrypt
            
        Returns:
            Dictionary with specified fields decrypted
        """
        decrypted_data = data.copy()
        
        for field in fields_to_decrypt:
            if field in decrypted_data and decrypted_data[field]:
                try:
                    decrypted_data[field] = self.decrypt(decrypted_data[field])
                except Exception:
                    # If decryption fails, field might not be encrypted
                    pass
        
        return decrypted_data


def generate_encryption_key() -> str:
    """
    Generate a new AES-256 encryption key
    
    Returns:
        Base64-encoded 256-bit key
    """
    key = os.urandom(32)  # 256 bits
    return base64.b64encode(key).decode('utf-8')


def get_encryption_service() -> EncryptionService:
    """Get encryption service instance"""
    return EncryptionService()


# PII fields that should be encrypted
PII_FIELDS = [
    'phone_number',
    'email',
    'address',
    'aadhar_number',
    'pan_number',
    'bank_account',
]
