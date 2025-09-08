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
    
    # Theta EdgeCloud Configuration
    ON_DEMAND_API_ACCESS_TOKEN: str = ""
    THETA_REQUEST_TIMEOUT: int = 20
    THETA_MAX_RETRIES: int = 2
    THETA_JSON_MODE: bool = False
    THETA_RATE_PER_MIN: int = 20
    THETA_RATE_BURST: int = 10
    THETA_SESSION_RATE_PER_MIN: int = 5
    THETA_SESSION_RATE_BURST: int = 5
    THETA_MAX_OUTPUT_TOKENS: int = 8000  # Conservative for Qwen 7B
    
    # Extraction Configuration
    SCHEMA_VERSION: str = "v1"
    EXTRACTOR_PROMPT_VERSION: str = "1.0"
    EXTRACTOR_MAX_TEXT_CHARS: int = 450000  # ~110k tokens budget
    EXTRACTOR_FAIL_THRESHOLD: float = 0.3  # 30% failure rate triggers degraded mode
    EXTRACTOR_MAX_CONCURRENT_SESSIONS: int = 4
    EXTRACTOR_MAX_PAGES_PER_SESSION: int = 100
    
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
    
    # On Demand API Configuration
    on_demand_api_access_token: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Create global settings instance
settings = Settings()
