"""
Pytest configuration and fixtures for the backend.
"""
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from bson import ObjectId

# 1. Setup Environment BEFORE any app imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
os.environ["MONGO_URI"] = "mongodb://mock-test-host:27017"
os.environ["DB_NAME"] = "csv_uploader_test"


@pytest.fixture(scope="function", autouse=True)
def setup_patches():
    """
    Global mocks for DB connections.
    Scope='function' ensures mocks are fresh for every test loop.
    """
    # Create the Master Mock for the DB
    mock_db = MagicMock()
    mock_fs_bucket = MagicMock()

    # --- Define Data Structure ---
    # This document MUST contain all fields accessed by the API
    mock_file_doc = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "filename": "test.csv",
        "status": "processed",
        "records_count": 0,
        "fields": ["col1", "col2"],
        "uploadDate": "2023-01-01T00:00:00"
    }

    # --- DB Returns ---
    mock_db.files.insert_one = AsyncMock(
        return_value=MagicMock(inserted_id=ObjectId("507f1f77bcf86cd799439011"))
    )
    mock_db.files.find_one = AsyncMock(return_value=mock_file_doc)
    mock_db.files.update_one = AsyncMock()
    mock_db.files.delete_one = AsyncMock()

    # --- Cursor Logic (for list_files) ---
    async def async_cursor_gen():
        yield mock_file_doc

    mock_cursor = MagicMock()
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.__aiter__.side_effect = async_cursor_gen
    mock_db.files.find.return_value = mock_cursor

    # --- GridFS Returns ---
    mock_fs_bucket.open_upload_stream = MagicMock()
    mock_fs_bucket.delete = MagicMock()
    
    mock_grid_out = MagicMock()
    mock_grid_out.read.return_value = b"" 
    mock_fs_bucket.find.return_value = [mock_grid_out]

    # --- Start Patches ---
    # We patch the SOURCE definitions in `app.db.mongo`.
    # Because we delayed the app import (see below), these patches will be active
    # when the app modules are first loaded, ensuring they pick up the Mocks.
    patches = [
        patch("app.db.mongo.client", MagicMock()),
        patch("app.db.mongo.db", mock_db),
        patch("app.db.mongo.fs_bucket", mock_fs_bucket),
        patch("app.db.mongo.GridFSBucket", MagicMock(return_value=mock_fs_bucket)),
    ]

    for p in patches:
        p.start()

    yield

    for p in patches:
        p.stop()


@pytest.fixture
def client():
    """
    Create a TestClient. 
    Importing app inside the fixture ensures patches are active during import.
    """
    # pylint: disable=import-outside-toplevel
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)
