"""
Application configuration settings.
"""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application configuration settings.
    Reads from environment variables or uses default values.
    """

    PROJECT_NAME: str = "CSV Engine API"
    API_V1_STR: str = "/api/v1"

    # Database Settings
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DB_NAME: str = os.getenv("DB_NAME", "csv_engine_db")

    # File Constraints
    MAX_FILE_SIZE_MB: int = 50

    @property
    def max_file_size_bytes(self) -> int:
        """Returns the max file size in bytes."""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024


settings = Settings()
