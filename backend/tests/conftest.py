"""
Pytest configuration and global fixtures.
"""

import sys
import os

# 1. Add the project root (backend) to sys.path immediately.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
import pytest
from bson import ObjectId
from app.db.mongo import db_manager  # Import the REAL singleton


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_db_manager():
    """
    Mocks the Singleton DatabaseManager IN-PLACE.
    """
    # 1. Create Mocks
    mock_fs = MagicMock()

    # Configure Upload Stream
    mock_upload_stream = AsyncMock()
    mock_upload_stream._id = ObjectId()
    mock_fs.open_upload_stream.return_value = mock_upload_stream

    # Configure Download Stream
    mock_download_stream = MagicMock()
    # Default behavior: return a simple valid CSV to prevent processing crashes
    mock_download_stream.read = AsyncMock(return_value=b"field1,field2\nvalue1,value2")

    # Ensure open_download_stream returns an awaitable that resolves to our stream mock
    mock_fs.open_download_stream = AsyncMock(return_value=mock_download_stream)

    mock_fs.delete = AsyncMock()
    mock_files_coll = AsyncMock()

    mock_db_obj = MagicMock()
    mock_db_obj.files = mock_files_coll

    # 2. Save Original State
    original_fs = db_manager.fs_bucket
    original_db = db_manager.db

    # 3. Apply Mocks
    db_manager.fs_bucket = mock_fs
    db_manager.db = mock_db_obj

    # 4. Patch Encryption to be Pass-through
    # FIX: Updated paths to point to 'app.utils.storage' instead of 'app.services.storage'
    with patch("app.utils.storage.encrypt_data", side_effect=lambda x: x), patch(
        "app.utils.storage.decrypt_data", side_effect=lambda x: x
    ):

        yield db_manager

    # 5. Teardown
    db_manager.fs_bucket = original_fs
    db_manager.db = original_db
