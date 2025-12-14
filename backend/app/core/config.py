"""
Application configuration settings.
"""

# import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application configuration settings.
    Reads from environment variables or uses default values.
    """

    # pylint: disable=too-few-public-methods

    PROJECT_NAME: str = "CSV Engine API"
    API_V1_STR: str = "/api/v1"

    # Database Settings
    # Pydantic automatically reads these from env vars
    MONGO_URI: str = "mongodb://localhost:27017"
    DB_NAME: str = "csv_engine_db"

    # Added to match your .env file and fix validation errors
    MONGO_USER: Optional[str] = None
    MONGO_PASSWORD: Optional[str] = None

    # Security - CRITICAL: This was missing!
    ENCRYPTION_KEY: str = "change_me_in_production"

    # File Constraints
    MAX_FILE_SIZE_MB: int = 50

    @property
    def max_file_size_bytes(self) -> int:
        """Returns the max file size in bytes."""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    LOG_LEVEL: str = "INFO"

    class Config:
        case_sensitive = True
        env_file = ".env"
        # CRITICAL FIX: Ignore extra env vars (like internal docker vars)
        # instead of crashing the app
        extra = "ignore"


settings = Settings()
