import pytest
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch
from bson import ObjectId

# Add backend directory to path so 'app' module can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

# Set environment variables early
os.environ["MONGO_URI"] = "mongodb://localhost:27017"
os.environ["DB_NAME"] = "csv_uploader_test"

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
# For synchronous calls like .sort(), we need to return a mock with sort method
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

# Start patches before importing app
patcher_client = patch("app.db.mongo.client", mock_client)
patcher_db = patch("app.db.mongo.db", mock_db)
patcher_fs = patch("app.db.mongo.fs_bucket", mock_fs_bucket)

patcher_client.start()
patcher_db.start()
patcher_fs.start()

# Import app AFTER patches are started
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Create test client with mocked MongoDB - works with Starlette 0.36+"""
    # TestClient in newer versions doesn't support context manager
    # Just return the client directly
    return TestClient(app)


# Register cleanup
def pytest_configure(config):
    """Register finalizer to stop patches."""

    def stop_patches():
        patcher_client.stop()
        patcher_db.stop()
        patcher_fs.stop()

    config.addinivalue_line("markers", "cleanup")


pytest.register_assert_rewrite("conftest")
