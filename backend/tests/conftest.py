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
def mock_mongo_infrastructure():
    """
    Patches the Motor Client and GridFSBucket classes globally.
    This prevents the real database connection from ever being established.
    """
    # --- Define Data Structure ---
    # This mock document satisfies all API requirements (preventing KeyError)
    mock_file_doc = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "filename": "test.csv",
        "status": "processed",
        "records_count": 0,
        "fields": ["col1", "col2"],
        "uploadDate": "2023-01-01T00:00:00"
    }

    # --- Create Mocks ---
    mock_db = MagicMock()
    mock_client_instance = MagicMock()
    # Ensure client['db_name'] returns our mock_db
    mock_client_instance.__getitem__.return_value = mock_db
    
    # Configure DB methods
    mock_db.files.insert_one = AsyncMock(
        return_value=MagicMock(inserted_id=ObjectId("507f1f77bcf86cd799439011"))
    )
    mock_db.files.find_one = AsyncMock(return_value=mock_file_doc)
    mock_db.files.update_one = AsyncMock()
    mock_db.files.delete_one = AsyncMock()

    # Configure Cursor (for list_files)
    async def async_cursor_gen():
        """Yield mock documents asynchronously."""
        yield mock_file_doc

    mock_cursor = MagicMock()
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.__aiter__.side_effect = async_cursor_gen
    mock_db.files.find.return_value = mock_cursor

    # Configure GridFS
    mock_fs_bucket = MagicMock()
    mock_fs_bucket.open_upload_stream = MagicMock()
    mock_fs_bucket.delete = MagicMock()
    mock_grid_out = MagicMock()
    mock_grid_out.read.return_value = b"" 
    mock_fs_bucket.find.return_value = [mock_grid_out]

    # --- Apply Patches ---
    # 1. Patch the AsyncIOMotorClient CLASS. 
    #    When app.db.mongo does 'client = AsyncIOMotorClient(...)', it gets our mock.
    with patch("motor.motor_asyncio.AsyncIOMotorClient", return_value=mock_client_instance), \
         patch("gridfs.GridFSBucket", return_value=mock_fs_bucket):
        
        yield


@pytest.fixture
def client():
    """
    Create a TestClient. 
    Importing app inside the fixture ensures it uses the patched classes.
    """
    # pylint: disable=import-outside-toplevel
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)
