"""
Configuration module for the Trading Bot API
Loads environment variables and provides configuration settings
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 5000
    api_env: str = "development"

    # CORS Configuration
    allowed_origins: str = "http://localhost:3005,http://localhost:3000"
    allowed_credentials: bool = True

    # Database Configuration
    db_host: str
    db_port: int = 3306
    db_name: str
    db_user: str
    db_password: str

    # JWT Configuration
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_days: int = 7

    # Encryption Configuration
    encryption_key: str

    # Firebase Configuration
    firebase_credentials_path: str = ""
    firebase_credentials_json: str = ""

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_period: int = 900

    @property
    def database_url(self) -> str:
        """Generate database connection URL"""
        return f"mysql+pymysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.api_env == "production"

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
