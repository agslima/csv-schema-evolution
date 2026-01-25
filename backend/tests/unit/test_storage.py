"""
Unit tests for storage security (Encryption/Decryption).
"""

from unittest.mock import patch, AsyncMock, MagicMock, call
import pytest
from bson import ObjectId

from app.repositories import file_repository


@pytest.mark.asyncio
async def test_save_file_encrypts_data(mock_db_manager):
    """
    Tests if the file is encrypted before being saved to GridFS.
    """
    # 1. Setup
    filename = "test_secure.csv"
    raw_content = b"user,email\n1,test@test.com"

    # Mock the GridFS upload stream
    grid_in_mock = AsyncMock()
    # pylint: disable=protected-access
    grid_in_mock._id = ObjectId()

    # open_upload_stream is synchronous in Motor (returns a stream), so simple return_value works
    mock_db_manager.fs_bucket.open_upload_stream.return_value = grid_in_mock

    # 2. Execute and Intercept Encryption
    with patch("app.repositories.file_repository.encrypt_data") as mock_encrypt:
        mock_encrypt.return_value = b"ENCRYPTED_BYTES"

        file_id = await file_repository.save_file(raw_content, filename)

        # 3. Asserts
        mock_encrypt.assert_called_once_with(raw_content)
        grid_in_mock.write.assert_awaited_once_with(b"ENCRYPTED_BYTES")
        assert file_id == grid_in_mock._id


@pytest.mark.asyncio
async def test_get_file_decrypts_data(mock_db_manager):
    """
    Tests if the file is decrypted when read from GridFS.
    """
    # 1. Setup
    file_id = str(ObjectId())
    encrypted_content = b"ENCRYPTED_BYTES"

    # Mock the download stream object
    grid_out_mock = MagicMock()
    grid_out_mock.read = AsyncMock(return_value=encrypted_content)

    # --- FIX START ---
    # The app code awaits this call: await open_download_stream(oid)
    # Therefore, open_download_stream must be an AsyncMock (or return a Future).
    # Setting it to AsyncMock(return_value=...) ensures calling it returns a coroutine
    # that resolves to 'grid_out_mock'.
    mock_db_manager.fs_bucket.open_download_stream = AsyncMock(
        return_value=grid_out_mock
    )
    # --- FIX END ---

    # 2. Execute
    with patch("app.repositories.file_repository.decrypt_data") as mock_decrypt:
        mock_decrypt.return_value = b"original,content"

        result = await file_repository.get_file_content_as_string(file_id)

        # 3. Asserts
        mock_decrypt.assert_called_once_with(encrypted_content)
        assert result == "original,content"


@pytest.mark.asyncio
async def test_delete_file_success(mock_db_manager):
    """Test successful deletion of metadata and gridfs content."""
    fake_id = str(ObjectId())
    processed_id = ObjectId()
    mock_doc = {"_id": ObjectId(fake_id), "processed_fs_id": processed_id}

    mock_db_manager.db.files.find_one = AsyncMock(return_value=mock_doc)

    # Mock delete_one to return deleted_count=1
    mock_db_manager.db.files.delete_one.return_value.deleted_count = 1

    # Execute
    result = await file_repository.delete_file(fake_id)

    assert result is True
    # Ensure GridFS delete was called
    mock_db_manager.fs_bucket.delete.assert_has_calls(
        [call(ObjectId(fake_id)), call(processed_id)],
        any_order=True,
    )


@pytest.mark.asyncio
async def test_delete_file_not_found_in_metadata(mock_db_manager):
    """Test deletion when file does not exist in metadata."""
    fake_id = str(ObjectId())

    mock_db_manager.db.files.find_one = AsyncMock(return_value=None)

    # Execute
    result = await file_repository.delete_file(fake_id)

    assert result is False
    mock_db_manager.db.files.delete_one.assert_not_called()
    # GridFS delete should NOT be called if metadata wasn't found
    mock_db_manager.fs_bucket.delete.assert_not_called()
