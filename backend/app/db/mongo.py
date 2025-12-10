import os
from motor.motor_asyncio import AsyncIOMotorClient
from gridfs import GridFSBucket
from bson import ObjectId

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017")
DB_NAME = os.getenv("DB_NAME", "csv_uploader")

client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

# Lazy initialization of fs_bucket to avoid issues with mocking in tests
_fs_bucket = None


def _get_fs_bucket():
    """Get or initialize GridFS bucket (lazy initialization)."""
    global _fs_bucket
    if _fs_bucket is None:
        _fs_bucket = GridFSBucket(db)
    return _fs_bucket


# Create a proxy object that delegates to the real fs_bucket
class _FSBucketProxy:
    """Proxy for GridFSBucket to enable lazy initialization."""

    def __getattr__(self, name):
        return getattr(_get_fs_bucket(), name)

    def __call__(self, *args, **kwargs):
        return _get_fs_bucket()(*args, **kwargs)


fs_bucket = _FSBucketProxy()
