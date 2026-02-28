"""SQLAlchemy custom types for encrypted fields"""
from sqlalchemy import TypeDecorator, String
from app.security.encryption import get_encryption_service


class EncryptedString(TypeDecorator):
    """SQLAlchemy type for encrypted string fields"""
    
    impl = String
    cache_ok = True
    
    def __init__(self, length=None, **kwargs):
        """
        Initialize encrypted string type
        
        Args:
            length: Maximum length of encrypted data (should be larger than plaintext)
        """
        # Encrypted data is larger due to IV and base64 encoding
        # Rule of thumb: encrypted_length = (plaintext_length + 16) * 1.5
        if length:
            length = int(length * 2)  # Double the length for safety
        super().__init__(length=length, **kwargs)
        self._encryption_service = None
    
    @property
    def encryption_service(self):
        """Lazy load encryption service"""
        if self._encryption_service is None:
            self._encryption_service = get_encryption_service()
        return self._encryption_service
    
    def process_bind_param(self, value, dialect):
        """Encrypt value before storing in database"""
        if value is None:
            return None
        return self.encryption_service.encrypt(str(value))
    
    def process_result_value(self, value, dialect):
        """Decrypt value when retrieving from database"""
        if value is None:
            return None
        try:
            return self.encryption_service.decrypt(value)
        except Exception:
            # If decryption fails, return None or original value
            # This handles cases where data might not be encrypted yet
            return None
