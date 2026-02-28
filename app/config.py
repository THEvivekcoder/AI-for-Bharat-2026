"""Application configuration"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "BharatSahayak"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"
    
    # Database
    database_url: str
    database_pool_size: int = 20
    database_max_overflow: int = 10
    
    # Redis
    redis_url: str
    redis_max_connections: int = 50
    
    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # OpenAI (for RAG/LLM)
    openai_api_key: str = ""
    
    # TLS/HTTPS Configuration
    tls_enabled: bool = False
    tls_cert_path: str = ""
    tls_key_path: str = ""
    tls_ca_cert_path: str = ""
    
    # Encryption
    encryption_key: str = ""  # AES-256 encryption key (base64 encoded)

    # ✅ THIS IS THE IMPORTANT PART
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()