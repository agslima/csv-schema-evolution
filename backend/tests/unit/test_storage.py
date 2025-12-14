"""
Unit tests for storage security (Encryption/Decryption).
"""

from io import BytesIO
from unittest.mock import patch, AsyncMock, MagicMock
import pytest
from bson import ObjectId
from fastapi import UploadFile

from app.utils import storage


@pytest.mark.asyncio
async def test_save_file_encrypts_data(mock_db_manager):
    """
    Tests if the file is encrypted before being saved to GridFS.
    """
    # 1. Setup
    filename = "test_secure.csv"
    raw_content = b"user,email\n1,test@test.com"

    # Simulate a FastAPI UploadFile
    file_obj = UploadFile(filename=filename, file=BytesIO(raw_content))

    # Mock the GridFS upload stream
    grid_in_mock = AsyncMock()
    # pylint: disable=protected-access
    grid_in_mock._id = ObjectId()

    # open_upload_stream is synchronous in Motor (returns a stream), so simple return_value works
    mock_db_manager.fs_bucket.open_upload_stream.return_value = grid_in_mock

    # 2. Execute and Intercept Encryption
    with patch("app.utils.storage.encrypt_data") as mock_encrypt:
        mock_encrypt.return_value = b"ENCRYPTED_BYTES"

        file_id = await storage.save_file_to_gridfs(file_obj)

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
    with patch("app.utils.storage.decrypt_data") as mock_decrypt:
        mock_decrypt.return_value = b"original,content"

        result = await storage.get_file_content_as_string(file_id)

        # 3. Asserts
        mock_decrypt.assert_called_once_with(encrypted_content)
        assert result == "original,content"
