import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bson import ObjectId
from app.services import csv_processor, sanitize

# ==========================================
# 1. Sanitize Tests (Unit Logic)
# ==========================================


def test_sanitize_value():
    """Test CSV injection prevention for dangerous prefixes."""
    assert sanitize.sanitize_value("=CMD") == "'=CMD"
    assert sanitize.sanitize_value("+SUM") == "'+SUM"
    assert sanitize.sanitize_value("-SYSTEM") == "'-SYSTEM"
    assert sanitize.sanitize_value("@IMPORT") == "'@IMPORT"
    assert sanitize.sanitize_value("normal") == "normal"
    assert sanitize.sanitize_value("") == ""
    assert sanitize.sanitize_value("123") == "123"


def test_sanitize_value_edge_cases():
    """Test sanitize with edge cases."""
    assert sanitize.sanitize_value("=") == "'="
    assert sanitize.sanitize_value("text=value") == "text=value"
    assert sanitize.sanitize_value("===DANGER") == "'===DANGER"


# ==========================================
# 2. Processor Tests (Integration Logic)
# ==========================================


@pytest.fixture
def mock_mongo():
    """
    Fixture to mock DB and FS_Bucket.
    Yields tuple (mock_db, mock_fs_bucket).
    """
    with patch("app.services.csv_processor.db") as mock_db, patch(
        "app.services.csv_processor.fs_bucket"
    ) as mock_fs:

        # Default DB behavior
        mock_db.files = MagicMock()
        mock_db.files.find_one = AsyncMock(
            return_value={
                "_id": ObjectId(),
                "filename": "test.csv",
                "status": "pending",
            }
        )
        mock_db.files.update_one = AsyncMock()

        yield mock_db, mock_fs


@pytest.mark.asyncio
async def test_process_csv_sync_gridfs(mock_mongo):
    """
    Test the standard PyMongo (Sync) path where fs_bucket returns an iterable.
    """
    mock_db, mock_fs = mock_mongo
    file_id = "507f1f77bcf86cd799439011"

    # Mock Content
    csv_content = b"field1,value1\nfield2,value2\n"

    # Mock Sync GridOut
    mock_out = MagicMock()
    mock_out.read.return_value = csv_content  # Sync read

    # Mock fs_bucket.find returning a list (Sync Iterable)
    mock_fs.find.return_value = [mock_out]

    # Run
    records = await csv_processor.process_csv(file_id)

    # Assertions
    assert len(records) == 1
    assert records[0]["field1"] == "value1"

    # Verify DB Update
    mock_db.files.update_one.assert_called_once()
    call_args = mock_db.files.update_one.call_args[0]
    assert call_args[1]["$set"]["status"] == "processed"
    assert call_args[1]["$set"]["records_count"] == 1


@pytest.mark.asyncio
async def test_process_csv_async_gridfs(mock_mongo):
    """
    Test the Motor (Async) path where fs_bucket returns an async cursor.
    This ensures the 'inspect.iscoroutinefunction' logic works.
    """
    mock_db, mock_fs = mock_mongo
    file_id = "507f1f77bcf86cd799439011"

    csv_content = b"col_a,col_b\nval_a,val_b\n"

    # Mock Async GridOut
    mock_out = MagicMock()
    # read() is a coroutine in Motor
    mock_out.read = AsyncMock(return_value=csv_content)

    # Mock Async Cursor
    mock_cursor = MagicMock()
    # to_list() is a coroutine in Motor
    mock_cursor.to_list = AsyncMock(return_value=[mock_out])

    mock_fs.find.return_value = mock_cursor

    # Run
    records = await csv_processor.process_csv(file_id)

    # Assertions
    assert len(records) == 1
    assert records[0]["col_a"] == "val_a"

    # Verify async calls were made
    mock_cursor.to_list.assert_awaited_once()
    mock_out.read.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_csv_with_injection(mock_mongo):
    """Test CSV processing sanitizes dangerous values."""
    mock_db, mock_fs = mock_mongo
    file_id = "507f1f77bcf86cd799439011"

    # Malicious CSV content
    csv_content = b"formula,=MALICIOUS()\nemail,+CMD\n"

    # Setup Sync GridFS (simpler for this test)
    mock_out = MagicMock()
    mock_out.read.return_value = csv_content
    mock_fs.find.return_value = [mock_out]

    records = await csv_processor.process_csv(file_id)

    assert len(records) >= 1
    record = records[0]
    # Check that values were sanitized
    assert record["formula"] == "'=MALICIOUS()"
    assert record["email"] == "'+CMD"


@pytest.mark.asyncio
async def test_process_csv_id_field_grouping(mock_mongo):
    """Test grouping rows into records based on ID field."""
    mock_db, mock_fs = mock_mongo

    # CSV where 'id' appears twice, implying two separate records
    # record 1: id=1, name=bob
    # record 2: id=2, name=alice
    csv_content = b"id,1\nname,bob\nid,2\nname,alice\n"

    mock_out = MagicMock()
    mock_out.read.return_value = csv_content
    mock_fs.find.return_value = [mock_out]

    # Run with id_field specified
    records = await csv_processor.process_csv("dummy_id", id_field="id")

    assert len(records) == 2
    assert records[0]["id"] == "1"
    assert records[0]["name"] == "bob"
    assert records[1]["id"] == "2"
    assert records[1]["name"] == "alice"
