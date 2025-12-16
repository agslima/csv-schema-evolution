"""
Application configuration settings.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration settings.
    Reads from environment variables or uses default values.
    """

    # pylint: disable=too-few-public-methods

    PROJECT_NAME: str = "CSV Engine API"
    API_V1_STR: str = "/api/v1"

    # Database Settings
    MONGO_URI: str = "mongodb://localhost:27017"
    DB_NAME: str = "csv_engine_db"
    MONGO_USER: Optional[str] = None
    MONGO_PASSWORD: Optional[str] = None

    # Security
    ENCRYPTION_KEY: str = "change_me_in_production"

    # File Constraints
    MAX_FILE_SIZE_MB: int = 50

    LOG_LEVEL: str = "INFO"

    @property
    def max_file_size_bytes(self) -> int:
        """
        Calculates the maximum file size in bytes based on the MB setting.
        """
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    model_config = SettingsConfigDict(
        case_sensitive=True, env_file=".env", extra="ignore"
    )


settings = Settings()
