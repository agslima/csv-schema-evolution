"""
MongoDB database connection manager.
Handles the AsyncIOMotorClient lifecycle and GridFS initialization.
"""

import logging

# FIX: Import the Async GridFS class from motor, not the sync one from gridfs
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from app.core.config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Singleton manager for MongoDB connection and GridFS bucket.
    """

    client: AsyncIOMotorClient = None
    db = None
    # FIX: Update type hint to AsyncIOMotorGridFSBucket
    fs_bucket: AsyncIOMotorGridFSBucket = None

    def connect(self):
        """Establishes the connection to MongoDB."""
        try:
            self.client = AsyncIOMotorClient(settings.MONGO_URI)
            self.db = self.client[settings.DB_NAME]

            # FIX: Initialize the Async Bucket
            # The standard 'GridFSBucket(self.db)' fails because self.db is async
            self.fs_bucket = AsyncIOMotorGridFSBucket(self.db)

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
