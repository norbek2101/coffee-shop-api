from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables.
    See .env file for actual values.
    """
    
    # Database
    DATABASE_URL: str
    
    # PostgreSQL credentials (for Docker)
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    
    # JWT Settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Verification
    VERIFICATION_CODE_EXPIRE_HOURS: int = 24
    
    # Auto-cleanup for unverified users
    UNVERIFIED_USER_DELETE_DAYS: int = 2
    
    # Application
    APP_NAME: str = "Coffee Shop API"
    DEBUG: bool = False
    
    # Celery / Background tasks
    # In production, override these via environment variables
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  


# Singleton instance
settings = Settings()
