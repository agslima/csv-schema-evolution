"""
Pytest configuration and global fixtures.
"""

import asyncio
from unittest.mock import MagicMock, AsyncMock
import pytest
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
    This ensures all modules (storage, cleanup) see the mocks 
    regardless of how they imported db_manager.
    """
    # 1. Create Mocks
    mock_fs = MagicMock()
    mock_fs.open_upload_stream.return_value = AsyncMock()
    mock_fs.open_download_stream.return_value = AsyncMock()
    mock_fs.delete = AsyncMock()

    mock_files_coll = AsyncMock()
    
    mock_db_obj = MagicMock()
    mock_db_obj.files = mock_files_coll

    # 2. Save Original State
    original_fs = db_manager.fs_bucket
    original_db = db_manager.db

    # 3. Apply Mocks to the Singleton Instance
    db_manager.fs_bucket = mock_fs
    db_manager.db = mock_db_obj

    yield db_manager

    # 4. Teardown (Restore Original)
    db_manager.fs_bucket = original_fs
    db_manager.db = original_db
