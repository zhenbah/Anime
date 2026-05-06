from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    # Project
    PROJECT_NAME: str = "Enterprise Scraping System"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Database
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DB: str = os.getenv("MONGODB_DB", "scraping_db")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # API
    API_V1_STR: str = "/api/v1"
    CORS_ORIGINS: List[str] = ["*"]
    
    # Scraping
    MAX_CONCURRENT_REQUESTS: int = 100
    REQUEST_TIMEOUT: int = 30
    RETRY_COUNT: int = 3
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    # Proxy
    PROXY_ENABLED: bool = False
    PROXY_LIST: List[str] = []
    
    # Headless Browser
    HEADLESS: bool = True
    BROWSER_TIMEOUT: int = 60
    
    # Queue
    QUEUE_NAME: str = "scraping_queue"
    PRIORITY_QUEUE_NAME: str = "scraping_priority_queue"
    
    # Monitoring
    LOG_LEVEL: str = "INFO"
    METRICS_ENABLED: bool = True
    
    # Scheduler
    SCHEDULER_ENABLED: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()