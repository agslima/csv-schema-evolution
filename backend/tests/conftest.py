"""
Pytest configuration and fixtures for the backend.
"""

import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from bson import ObjectId

# pylint: disable=no-member
# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

# Set environment variables early
os.environ["MONGO_URI"] = "mongodb://mock-test-host:27017"
os.environ["DB_NAME"] = "csv_uploader_test"
# pylint: enable=no-member

# Import app AFTER setting env vars
# pylint: disable=wrong-import-position
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="function", autouse=True)
def setup_patches():
    """
    Global mocks for DB connections.
    Scope='function' ensures mocks are fresh for every test loop.
    """
    mock_db = MagicMock()
    mock_fs_bucket = MagicMock()

    # --- 1. DB MOCK Returns (Fixed KeyError) ---
    # We create a full document that satisfies the API's requirements
    mock_file_doc = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "filename": "test.csv",
        "status": "processed",
        "records_count": 0,  # Fixed: Added missing key
        "fields": ["col1", "col2"],  # Fixed: Added missing key
        "uploadDate": "2023-01-01T00:00:00",
    }

    mock_db.files.insert_one = AsyncMock(
        return_value=MagicMock(inserted_id=ObjectId("507f1f77bcf86cd799439011"))
    )
    # find_one must return the full doc to avoid KeyError in get_file_stream
    mock_db.files.find_one = AsyncMock(return_value=mock_file_doc)
    mock_db.files.update_one = AsyncMock()
    mock_db.files.delete_one = AsyncMock()

    # --- 2. Cursor Setup (Fixed ServerTimeout/Async Loop) ---
    # This generator mocks the 'async for doc in cursor' behavior
    async def async_cursor_gen():
        yield mock_file_doc

    mock_cursor = MagicMock()
    mock_cursor.sort.return_value = mock_cursor
    # Assign the async generator to __aiter__
    mock_cursor.__aiter__.side_effect = async_cursor_gen
    mock_db.files.find.return_value = mock_cursor

    # --- 3. GridFS Returns ---
    mock_fs_bucket.open_upload_stream = MagicMock()
    mock_fs_bucket.delete = MagicMock()

    mock_grid_out = MagicMock()
    mock_grid_out.read.return_value = b""
    mock_fs_bucket.find.return_value = [mock_grid_out]

    # --- 4. APPLY PATCHES ---
    patches = [
        # Patch services (already handled)
        patch("app.services.storage.db", mock_db),
        patch("app.services.storage.fs_bucket", mock_fs_bucket),
        patch("app.services.csv_processor.db", mock_db),
        patch("app.services.csv_processor.fs_bucket", mock_fs_bucket),
        # Patch Base DB definitions
        patch("app.db.mongo.db", mock_db),
        patch("app.db.mongo.fs_bucket", mock_fs_bucket),
        patch("app.db.mongo.GridFSBucket", MagicMock(return_value=mock_fs_bucket)),
        # CRITICAL FIX: Patch the API layer directly.
        # The API imports 'db' directly, so we must intercept it here to prevent
        # it from using the real connection string.
        patch("app.api.v1.files.db", mock_db),
    ]

    for patcher in patches:
        patcher.start()

    yield

    for patcher in patches:
        patcher.stop()


@pytest.fixture
def client():
    return TestClient(app)
