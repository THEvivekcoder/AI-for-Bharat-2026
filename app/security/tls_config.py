"""TLS/HTTPS configuration for FastAPI"""
import ssl
from pathlib import Path
from typing import Optional
from app.config import get_settings

settings = get_settings()


class TLSConfig:
    """TLS/HTTPS configuration manager"""
    
    def __init__(
        self,
        cert_path: Optional[str] = None,
        key_path: Optional[str] = None,
        ca_cert_path: Optional[str] = None
    ):
        """
        Initialize TLS configuration
        
        Args:
            cert_path: Path to SSL certificate file
            key_path: Path to SSL private key file
            ca_cert_path: Path to CA certificate file (optional)
        """
        self.cert_path = cert_path or getattr(settings, 'tls_cert_path', None)
        self.key_path = key_path or getattr(settings, 'tls_key_path', None)
        self.ca_cert_path = ca_cert_path or getattr(settings, 'tls_ca_cert_path', None)
    
    def create_ssl_context(self) -> Optional[ssl.SSLContext]:
        """
        Create SSL context for HTTPS
        
        Returns:
            SSL context configured for TLS 1.3 or None if certs not available
        """
        if not self.cert_path or not self.key_path:
            return None
        
        # Verify certificate files exist
        cert_file = Path(self.cert_path)
        key_file = Path(self.key_path)
        
        if not cert_file.exists():
            raise FileNotFoundError(f"Certificate file not found: {self.cert_path}")
        if not key_file.exists():
            raise FileNotFoundError(f"Key file not found: {self.key_path}")
        
        # Create SSL context with TLS 1.3
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        
        # Set minimum TLS version to 1.3 (or 1.2 as fallback)
        try:
            context.minimum_version = ssl.TLSVersion.TLSv1_3
        except AttributeError:
            # Fallback for older Python versions
            context.minimum_version = ssl.TLSVersion.TLSv1_2
        
        # Load certificate and private key
        context.load_cert_chain(
            certfile=str(cert_file),
            keyfile=str(key_file)
        )
        
        # Load CA certificate if provided
        if self.ca_cert_path:
            ca_file = Path(self.ca_cert_path)
            if ca_file.exists():
                context.load_verify_locations(cafile=str(ca_file))
        
        # Set secure cipher suites
        context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
        
        return context
    
    def get_uvicorn_ssl_config(self) -> dict:
        """
        Get SSL configuration for uvicorn
        
        Returns:
            Dictionary with ssl_keyfile and ssl_certfile paths
        """
        if not self.cert_path or not self.key_path:
            return {}
        
        return {
            'ssl_keyfile': self.key_path,
            'ssl_certfile': self.cert_path,
            'ssl_ca_certs': self.ca_cert_path if self.ca_cert_path else None,
            'ssl_version': ssl.PROTOCOL_TLS_SERVER,
        }
    
    @property
    def is_configured(self) -> bool:
        """Check if TLS is properly configured"""
        return bool(self.cert_path and self.key_path)


def get_tls_config() -> TLSConfig:
    """Get TLS configuration instance"""
    return TLSConfig()
