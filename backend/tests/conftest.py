import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_db_manager():
    """
    Mocks the Singleton DatabaseManager.
    Crucial for Unit Tests to avoid needing a real Mongo connection.
    """
    with pytest.patch("app.services.storage.db_manager") as mock_db:
        # Mock GridFS Bucket
        mock_bucket = MagicMock()
        mock_bucket.open_upload_stream.return_value = AsyncMock()
        mock_bucket.open_download_stream.return_value = AsyncMock()
        mock_bucket.delete = AsyncMock()
        
        mock_db.fs_bucket = mock_bucket
        
        # Mock Standard DB Collections
        mock_collection = AsyncMock()
        mock_db.db.files = mock_collection
        
        yield mock_db
