import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timedelta, timezone
from app.services.cleanup import delete_expired_files

@pytest.mark.asyncio
async def test_cleanup_deletes_old_files(mock_db_manager):
    """
    Tests if the cleanup job finds old files and calls delete.
    """
    # 1. Setup - Mock Mongo cursor
    # Create a fake "document" representing an expired file
    expired_file_id = "507f1f77bcf86cd799439011"
    mock_doc = {"_id": expired_file_id}
    
    # Configure async cursor mock
    mock_cursor = AsyncMock()
    mock_cursor.__aiter__.return_value = [mock_doc]
    
    # Inject cursor into find
    mock_db_manager.db.files.find.return_value = mock_cursor

    # 2. Execute intercepting storage.delete_file
    with patch("app.services.cleanup.storage.delete_file", new_callable=AsyncMock) as mock_delete_fn:
        await delete_expired_files()
        
        # 3. Asserts
        # Verify if database was queried with date criteria
        mock_db_manager.db.files.find.assert_called_once()
        args, _ = mock_db_manager.db.files.find.call_args
        query = args[0]
        
        # Ensure query uses $lt (less than) on created_at
        assert "created_at" in query
        assert "$lt" in query["created_at"]
        
        # Verify if delete function was called with correct ID
        mock_delete_fn.assert_called_once_with(expired_file_id)
