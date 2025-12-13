"""
Unit tests for the storage service.
"""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from bson import ObjectId
from app.utils import storage

# pylint: disable=redefined-outer-name

# Mock content slightly larger than our test limit
TEST_LIMIT = 100
LARGE_CONTENT = b"x" * (TEST_LIMIT + 1)
VALID_CONTENT = b"valid content"
ENCRYPTED_CONTENT = b"encrypted_valid_content"


@pytest.fixture
def mock_deps():
    """Fixture to mock DB manager and Encryption functions."""
    with patch("app.utils.storage.db_manager") as mock_db_manager, patch(
        "app.utils.storage.encrypt_data"
    ) as mock_encrypt, patch("app.utils.storage.decrypt_data") as mock_decrypt:

        # Setup Files Collection Mocks
        mock_db_manager.db.files = MagicMock()
        mock_db_manager.db.files.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=ObjectId())
        )
        mock_db_manager.db.files.find_one = AsyncMock()
        mock_db_manager.db.files.update_one = AsyncMock()
        mock_db_manager.db.files.delete_one = AsyncMock()

        # Setup GridFS Mocks
        mock_fs = mock_db_manager.fs_bucket
        mock_fs.open_upload_stream = MagicMock()
        mock_fs.open_download_stream = MagicMock()
        mock_fs.delete = MagicMock()

        # Setup Encryption Mocks
        mock_encrypt.return_value = ENCRYPTED_CONTENT
        mock_decrypt.return_value = VALID_CONTENT

        yield mock_db_manager, mock_encrypt, mock_decrypt


@pytest.fixture
def mock_file():
    """Fixture to create a mock file object (like an UploadFile)."""
    file_mock = MagicMock()
    file_mock.filename = "test_data.csv"
    # read() must be awaitable
    file_mock.read = AsyncMock()
    return file_mock


@pytest.mark.asyncio
async def test_save_file_to_gridfs_success(mock_deps, mock_file):
    """Test saving a file under the size limit."""
    mock_db_manager, mock_encrypt, _ = mock_deps
    mock_fs = mock_db_manager.fs_bucket

    # Setup valid content
    mock_file.read.return_value = VALID_CONTENT

    # Patch config directly in storage module
    with patch("app.utils.storage.settings") as mock_settings:
        mock_settings.max_file_size_bytes = 1024 * 1024  # 1MB limit

        file_id = await storage.save_file_to_gridfs(mock_file)

    assert isinstance(file_id, ObjectId)

    # Verify Encryption was called
    mock_encrypt.assert_called_with(VALID_CONTENT)

    # Verify GridFS write used ENCRYPTED content
    mock_fs.open_upload_stream.assert_called_with("test_data.csv")
    upload_stream = mock_fs.open_upload_stream.return_value
    upload_stream.write.assert_awaited_with(ENCRYPTED_CONTENT)
    upload_stream.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_save_file_too_large(mock_deps, mock_file):
    """Test that saving a file exceeding the limit raises ValueError."""
    mock_db_manager, _, _ = mock_deps
    mock_fs = mock_db_manager.fs_bucket

    mock_file.read.return_value = LARGE_CONTENT

    # Patch the limit to be smaller than our content
    with patch("app.utils.storage.settings") as mock_settings:
        mock_settings.max_file_size_bytes = TEST_LIMIT

        with pytest.raises(ValueError, match="File exceeds maximum size"):
            await storage.save_file_to_gridfs(mock_file)

    # Ensure we didn't write to GridFS
    mock_fs.open_upload_stream.assert_not_called()


@pytest.mark.asyncio
async def test_create_file_metadata(mock_deps):
    """Test creating initial metadata."""
    mock_db_manager, _, _ = mock_deps
    file_id = ObjectId()

    result = await storage.create_file_metadata(file_id, "test.csv")

    assert result["_id"] == file_id
    assert result["filename"] == "test.csv"
    assert result["status"] == "pending"
    assert "created_at" in result

    mock_db_manager.db.files.insert_one.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_file_content_as_string_success(mock_deps):
    """Test retrieving and decrypting file content."""
    mock_db_manager, _, mock_decrypt = mock_deps
    mock_fs = mock_db_manager.fs_bucket
    test_id = str(ObjectId())

    # Mock GridFS output stream
    mock_grid_out = MagicMock()
    mock_grid_out.read = AsyncMock(return_value=ENCRYPTED_CONTENT)
    mock_fs.open_download_stream.return_value = mock_grid_out

    # Run function
    result = await storage.get_file_content_as_string(test_id)

    # Verify Decryption and Decoding
    mock_decrypt.assert_called_with(ENCRYPTED_CONTENT)
    assert result == VALID_CONTENT.decode("utf-8")


@pytest.mark.asyncio
async def test_delete_file_success(mock_deps):
    """Test full cleanup of file from DB and GridFS."""
    mock_db_manager, _, _ = mock_deps
    mock_db = mock_db_manager.db
    mock_fs = mock_db_manager.fs_bucket
    test_id = str(ObjectId())

    # Setup DB Delete to return count > 0
    mock_delete_result = MagicMock()
    mock_delete_result.deleted_count = 1
    mock_db.files.delete_one.return_value = mock_delete_result

    # Run Delete
    success = await storage.delete_file(test_id)

    assert success is True

    # Verify DB Delete
    mock_db.files.delete_one.assert_awaited_with({"_id": ObjectId(test_id)})

    # Verify GridFS Delete
    mock_fs.delete.assert_awaited_with(ObjectId(test_id))


@pytest.mark.asyncio
async def test_delete_file_not_found(mock_deps):
    """Test delete returns False if file metadata is missing."""
    mock_db_manager, _, _ = mock_deps
    mock_db = mock_db_manager.db
    mock_fs = mock_db_manager.fs_bucket

    # Setup DB Delete to return count 0
    mock_delete_result = MagicMock()
    mock_delete_result.deleted_count = 0
    mock_db.files.delete_one.return_value = mock_delete_result

    success = await storage.delete_file(str(ObjectId()))

    assert success is False
    mock_fs.delete.assert_not_called()
