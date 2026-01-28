"""
Unit tests for the cleanup service.
"""

# Standard library imports first
from unittest.mock import patch, AsyncMock, MagicMock

# Third-party imports second
import pytest

# Local application imports last
from app.services.cleanup import delete_expired_files


@pytest.mark.asyncio
async def test_cleanup_deletes_old_files(mock_db_manager):
    """
    Tests if the cleanup job finds old files and calls delete.
    """
    # 1. Setup - Mock Mongo cursor
    expired_file_id = "507f1f77bcf86cd799439011"
    mock_doc = {"_id": expired_file_id}

    # Define an async generator to simulate the MongoDB cursor
    async def mock_cursor_generator():
        yield mock_doc

    # --- KEY FIX ---
    # Convert 'find' to MagicMock so it returns the generator IMMEDIATELY
    # instead of returning a coroutine (which AsyncMock does by default).
    mock_db_manager.db.files.find = MagicMock(return_value=mock_cursor_generator())

    # 2. Execute intercepting file_repository.delete_file
    with patch(
        "app.services.cleanup.file_repository.delete_file", new_callable=AsyncMock
    ) as mock_delete_fn:
        await delete_expired_files()

        # 3. Asserts
        mock_db_manager.db.files.find.assert_called_once()
        args, _ = mock_db_manager.db.files.find.call_args
        query = args[0]

        # Ensure query uses $lt (less than) on created_at
        assert "created_at" in query
        assert "$lt" in query["created_at"]

        # Verify if delete function was called with correct ID
        mock_delete_fn.assert_called_once_with(expired_file_id)
