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


@pytest.fixture
def mock_mongo():
    """Fixture to mock the database and GridFS bucket."""
    with patch("app.services.storage.db") as mock_db, patch(
        "app.services.storage.fs_bucket"
    ) as mock_fs:

        # Setup Files Collection Mocks
        mock_db.files = MagicMock()
        mock_db.files.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=ObjectId())
        )
        mock_db.files.find_one = AsyncMock()
        mock_db.files.delete_one = AsyncMock()

        # Setup GridFS Mocks
        mock_fs.open_upload_stream = MagicMock()
        mock_fs.open_download_stream_by_name = MagicMock()
        mock_fs.find = MagicMock()
        mock_fs.delete = MagicMock()

        yield mock_db, mock_fs


@pytest.fixture
def mock_file():
    """Fixture to create a mock file object (like an UploadFile)."""
    file_mock = MagicMock()
    file_mock.filename = "test_data.csv"
    # read() must be awaitable
    file_mock.read = AsyncMock()
    return file_mock


@pytest.mark.asyncio
async def test_save_file_success(mock_mongo, mock_file):
    """Test saving a file under the size limit."""
    mock_db, mock_fs = mock_mongo

    # Setup valid content
    mock_file.read.return_value = VALID_CONTENT

    # We patch MAX_FILE_SIZE to ensure our small content is definitely "valid"
    # without relying on the real huge limit.
    with patch("app.services.storage.MAX_FILE_SIZE", 1024 * 1024):
        file_id = await storage.save_file(mock_file)

    assert isinstance(file_id, ObjectId)

    # Verify GridFS write
    mock_fs.open_upload_stream.assert_called_with("test_data.csv")
    upload_stream = mock_fs.open_upload_stream.return_value
    upload_stream.write.assert_called_with(VALID_CONTENT)
    upload_stream.close.assert_called_once()

    # Verify Metadata Insert
    mock_db.files.insert_one.assert_awaited_once()
    inserted_doc = mock_db.files.insert_one.call_args[0][0]
    assert inserted_doc["filename"] == "test_data.csv"
    assert inserted_doc["size"] == len(VALID_CONTENT)
    assert inserted_doc["status"] == "pending"


@pytest.mark.asyncio
async def test_save_file_too_large(mock_mongo, mock_file):
    """Test that saving a file exceeding the limit raises ValueError."""
    mock_db, mock_fs = mock_mongo

    mock_file.read.return_value = LARGE_CONTENT

    # Patch the limit to be smaller than our content
    with patch("app.services.storage.MAX_FILE_SIZE", TEST_LIMIT):
        with pytest.raises(ValueError, match="File exceeds maximum size"):
            await storage.save_file(mock_file)

    # Ensure we didn't write to DB or GridFS
    mock_fs.open_upload_stream.assert_not_called()
    mock_db.files.insert_one.assert_not_called()


@pytest.mark.asyncio
async def test_get_file_stream_found(mock_mongo):
    """Test retrieving an existing file stream."""
    mock_db, mock_fs = mock_mongo
    test_id = str(ObjectId())

    # Mock DB finding the file
    mock_db.files.find_one.return_value = {
        "_id": ObjectId(test_id),
        "filename": "test.csv",
    }

    # Mock GridFS opening the stream
    expected_stream = MagicMock()
    mock_fs.open_download_stream_by_name.return_value = expected_stream

    result = await storage.get_file_stream(test_id)

    assert result is not None
    stream, doc = result
    assert stream == expected_stream
    assert doc["filename"] == "test.csv"


@pytest.mark.asyncio
async def test_get_file_stream_not_found(mock_mongo):
    """Test retrieving a non-existent file returns None."""
    mock_db, _ = mock_mongo
    mock_db.files.find_one.return_value = None

    result = await storage.get_file_stream(str(ObjectId()))
    assert result is None


@pytest.mark.asyncio
async def test_delete_file_success(mock_mongo):
    """Test full cleanup of file from DB and GridFS."""
    mock_db, mock_fs = mock_mongo
    test_id = str(ObjectId())

    # 1. Setup DB to find the file doc
    mock_db.files.find_one.return_value = {
        "_id": ObjectId(test_id),
        "filename": "delete_me.csv",
    }

    # 2. Setup GridFS to find the actual binary chunks
    # Create a mock grid_file object that has an _id
    mock_grid_file = MagicMock()
    # pylint: disable=protected-access
    mock_grid_file._id = ObjectId()
    mock_fs.find.return_value = [mock_grid_file]

    # Run Delete
    success = await storage.delete_file(test_id)

    assert success is True

    # Verify DB Delete
    mock_db.files.delete_one.assert_awaited_with({"_id": ObjectId(test_id)})

    # Verify GridFS Delete (Iterating over cursor)
    mock_fs.find.assert_called_with({"filename": "delete_me.csv"})
    # pylint: disable=protected-access
    mock_fs.delete.assert_called_with(mock_grid_file._id)


@pytest.mark.asyncio
async def test_delete_file_not_found(mock_mongo):
    """Test delete returns False if file metadata is missing."""
    mock_db, mock_fs = mock_mongo
    mock_db.files.find_one.return_value = None

    success = await storage.delete_file(str(ObjectId()))

    assert success is False
    mock_db.files.delete_one.assert_not_called()
    mock_fs.delete.assert_not_called()
