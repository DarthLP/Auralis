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
    
    # AI Configuration
    THETA_EDGECLOUD_API_KEY: str = ""
    THETA_EDGECLOUD_URL: str = ""
    API_KEY_SCHEMA: str = ""  # Deep Seek API for Analysis
    
    # Scraper Configuration
    SCRAPER_MAX_PAGES: int = 100
    SCRAPER_MAX_DEPTH: int = 4
    SCRAPER_TIMEOUT: int = 10
    SCRAPER_RATE_SLEEP: float = 0.3
    SCRAPER_USER_AGENT: str = "AuralisBot/0.1 (+contact)"
    SCRAPER_MAX_RETRIES: int = 3
    SCRAPER_USE_REALISTIC_HEADERS: bool = True
    SCRAPER_ENABLE_JAVASCRIPT: bool = True
    SCRAPER_JS_WAIT_TIME: int = 1
    SCRAPER_LOG_LEVEL: str = "INFO"
    SCRAPER_LOG_FILE: str = "logs/scraper.log"
    
    # Download Configuration
    SCRAPER_DOWNLOAD_THRESHOLD: float = 0.5
    SCRAPER_DOWNLOAD_MAX_PAGES: int = 100
    
    # Core Crawl Configuration
    CORE_CRAWL_CONCURRENCY: int = 8
    CORE_CRAWL_BATCH_SIZE: int = 20
    CORE_CRAWL_MAX_CONTENT_SIZE: int = 15 * 1024 * 1024  # 15MB
    CORE_CRAWL_CONNECT_TIMEOUT: int = 5  # seconds
    CORE_CRAWL_READ_TIMEOUT: int = 20  # seconds
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Create global settings instance
settings = Settings()
