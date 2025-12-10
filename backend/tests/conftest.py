"""
Pytest configuration and fixtures for the backend.
"""

import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from bson import ObjectId

# pylint: disable=no-member
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

# Set environment variables early
os.environ["MONGO_URI"] = "mongodb://localhost:27017"
os.environ["DB_NAME"] = "csv_uploader_test"
# pylint: enable=no-member

# Import app AFTER setting env vars
# pylint: disable=wrong-import-position
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="function", autouse=True)
def setup_patches():
    """
    Apply mocks to SERVICES directly to override the already-imported db objects.
    Scope is 'function' to match pytest-asyncio's event loop lifecycle.
    """
    # Create fresh mocks
    mock_db = MagicMock()
    mock_fs_bucket = MagicMock()

    # --- DB MOCK SETUP ---
    mock_db.files.insert_one = AsyncMock(
        return_value=MagicMock(inserted_id=ObjectId("507f1f77bcf86cd799439011"))
    )

    mock_db.files.find_one = AsyncMock(
        return_value={
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "filename": "test.csv",
            "status": "processed",
            "records_count": 0,
            "fields": [],
        }
    )
    mock_db.files.update_one = AsyncMock()
    mock_db.files.delete_one = AsyncMock()

    mock_cursor = MagicMock()
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.__aiter__.return_value = iter([])
    mock_db.files.find.return_value = mock_cursor

    # --- GRIDFS MOCK SETUP ---
    mock_fs_bucket.open_upload_stream = MagicMock()
    mock_fs_bucket.open_download_stream_by_name = MagicMock()
    mock_fs_bucket.delete = MagicMock()

    mock_grid_out = MagicMock()
    mock_grid_out.read.return_value = b""
    mock_fs_bucket.find.return_value = [mock_grid_out]

    # --- APPLY PATCHES ---
    patches = [
        patch("app.services.storage.db", mock_db),
        patch("app.services.storage.fs_bucket", mock_fs_bucket),
        patch("app.services.csv_processor.db", mock_db),
        patch("app.services.csv_processor.fs_bucket", mock_fs_bucket),
        patch("app.db.mongo.db", mock_db),
        patch("app.db.mongo.fs_bucket", mock_fs_bucket),
        patch("app.db.mongo.GridFSBucket", MagicMock(return_value=mock_fs_bucket)),
    ]

    # Fix: Renamed 'p' to 'patcher' to satisfy C0103
    for patcher in patches:
        patcher.start()

    yield

    for patcher in patches:
        patcher.stop()


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)
