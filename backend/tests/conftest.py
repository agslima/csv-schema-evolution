"""
Pytest configuration and fixtures for the backend.
Sets up MongoDB mocks and environment variables.
"""
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from bson import ObjectId

# pylint: disable=no-member
# Add backend directory to path so 'app' module can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

# Set environment variables early
os.environ["MONGO_URI"] = "mongodb://localhost:27017"
os.environ["DB_NAME"] = "csv_uploader_test"
# pylint: enable=no-member

# --- MOCK SETUP ---
# Create mock objects
mock_client = MagicMock()
mock_db = MagicMock()
mock_fs_bucket = MagicMock()

# Create a valid ObjectId for testing
test_oid = ObjectId()

# Setup mock methods for db.files
mock_db.files = MagicMock()
mock_db.files.insert_one = AsyncMock(return_value=MagicMock(inserted_id=test_oid))
mock_db.files.find_one = AsyncMock(
    return_value={
        "_id": test_oid,
        "filename": "test.csv",
        "status": "processed",
        "records_count": 0,
        "fields": [],
    }
)
mock_db.files.update_one = AsyncMock()
mock_db.files.delete_one = AsyncMock()

# Mock find() to return async iterable or mock cursor
mock_cursor = MagicMock()
mock_cursor.sort.return_value = mock_cursor
mock_cursor.__aiter__.return_value = iter(
    [
        {
            "_id": test_oid,
            "filename": "test.csv",
            "status": "processed",
            "records_count": 0,
            "fields": [],
        }
    ]
)
mock_db.files.find.return_value = mock_cursor

# Setup mock methods for fs_bucket
mock_fs_bucket.open_upload_stream = MagicMock()
mock_fs_bucket.open_download_stream_by_name = MagicMock()

# Mock find() to return list with file-like object
mock_grid_out = MagicMock()
mock_grid_out.read.return_value = b"field1,value1\nfield2,value2\n"
mock_fs_bucket.find.return_value = [mock_grid_out]
mock_fs_bucket.delete = MagicMock()


@pytest.fixture(scope="session", autouse=True)
def setup_patches():
    """
    Apply mocks to app.db.mongo before the app is imported.
    Yields control to tests, then stops patches after session ends.
    """
    # 1. Patch the client and db instances
    patcher_client = patch("app.db.mongo.client", mock_client)
    patcher_db = patch("app.db.mongo.db", mock_db)
    # 2. Patch the fs_bucket variable (the proxy)
    patcher_fs = patch("app.db.mongo.fs_bucket", mock_fs_bucket)
    # 3. CRITICAL FIX: Patch the GridFSBucket CLASS.
    # This prevents the real GridFSBucket(db) from running and throwing TypeError
    patcher_gridfs_cls = patch("app.db.mongo.GridFSBucket")

    patcher_client.start()
    patcher_db.start()
    patcher_fs.start()
    # Configure the class mock to return our mock bucket instance
    mock_cls = patcher_gridfs_cls.start()
    mock_cls.return_value = mock_fs_bucket

    yield

    patcher_client.stop()
    patcher_db.stop()
    patcher_fs.stop()
    patcher_gridfs_cls.stop()


# pylint: disable=wrong-import-position
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app                   # noqa: E402


@pytest.fixture
def client():
    """Create test client with mocked MongoDB."""
    return TestClient(app)
