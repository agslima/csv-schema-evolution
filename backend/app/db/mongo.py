"""
MongoDB connection and GridFS bucket initialization.
"""

import os
from motor.motor_asyncio import AsyncIOMotorClient
from gridfs import GridFSBucket

# pylint: disable=no-member
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017")
DB_NAME = os.getenv("DB_NAME", "csv_uploader")
# pylint: enable=no-member

client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

# Lazy initialization of fs_bucket to avoid issues with mocking in tests
_GRID_FS_BUCKET = None


def _get_fs_bucket():
    """Get or initialize GridFS bucket (lazy initialization)."""
    global _GRID_FS_BUCKET  # pylint: disable=global-statement
    if _GRID_FS_BUCKET is None:
        _GRID_FS_BUCKET = GridFSBucket(db)
    return _GRID_FS_BUCKET


# Create a proxy object that delegates to the real fs_bucket
class _FSBucketProxy:
    """Proxy for GridFSBucket to enable lazy initialization."""

    def __getattr__(self, name):
        return getattr(_get_fs_bucket(), name)

    def __call__(self, *args, **kwargs):
        return _get_fs_bucket()(*args, **kwargs)


fs_bucket = _FSBucketProxy()
