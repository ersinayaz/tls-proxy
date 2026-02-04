"""
Configuration settings for TLS Proxy Service
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Authentication
    api_key: str = "change-me-in-production"
    
    # Session Management
    session_ttl: int = 3600  # Session timeout in seconds (1 hour)
    max_sessions: int = 100  # Maximum number of active sessions
    
    # Server Configuration
    port: int = 8000
    host: str = "0.0.0.0"
    
    # Request Configuration
    request_timeout: int = 30  # Request timeout in seconds
    
    # TLS Client Configuration
    client_identifier: str = "chrome_133"  # Chrome 133 profile
    random_tls_extension_order: bool = True  # Randomize TLS extensions for better fingerprint evasion
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
