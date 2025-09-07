from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """
    Application settings using Pydantic Settings.
    Loads from environment variables with sensible defaults.
    """
    
    # Application settings
    DEBUG: bool = False
    LOG_LEVEL: str = "info"
    ENVIRONMENT: str = "development"
    
    # Server configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database configuration
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@db:5432/auralis"
    
    # CORS configuration
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Convert comma-separated ALLOWED_ORIGINS to list"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    # AI Configuration (Future)
    THETA_EDGECLOUD_API_KEY: str = ""
    THETA_EDGECLOUD_URL: str = ""
    
    # Scraping Configuration (Future)
    SCRAPING_DELAY: float = 1.0  # Delay between requests in seconds
    MAX_RETRIES: int = 3
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Create global settings instance
settings = Settings()
