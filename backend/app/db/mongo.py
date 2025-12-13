"""
MongoDB database connection manager.
Handles the AsyncIOMotorClient lifecycle and GridFS initialization.
"""

import logging
from motor.motor_asyncio import AsyncIOMotorClient
from gridfs import GridFSBucket
from app.core.config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Singleton manager for MongoDB connection and GridFS bucket.
    """

    client: AsyncIOMotorClient = None
    db = None
    fs_bucket: GridFSBucket = None

    def connect(self):
        """Establishes the connection to MongoDB."""
        try:
            self.client = AsyncIOMotorClient(settings.MONGO_URI)
            self.db = self.client[settings.DB_NAME]
            # GridFSBucket requires the database object, not the client
            self.fs_bucket = GridFSBucket(self.db)
            logger.info("Successfully connected to MongoDB at %s", settings.MONGO_URI)
        # pylint: disable=broad-exception-caught
        except Exception as e:
            logger.error("Failed to connect to MongoDB: %s", e)
            raise

    def close(self):
        """Closes the MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed.")


db_manager = DatabaseManager()
