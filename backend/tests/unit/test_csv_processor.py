"""
Unit tests for CSV processor service.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bson import ObjectId
from app.services import csv_processor


@pytest.fixture
def mock_mongo():
    """
    Fixture to mock DB and FS_Bucket.
    Yields tuple (mock_db, mock_fs_bucket).
    """
    with patch("app.services.csv_processor.db") as mock_db, patch(
        "app.services.csv_processor.fs_bucket"
    ) as mock_fs:
        yield mock_db, mock_fs


# ... (keep existing synchronize tests like test_sanitize_value) ...
def test_sanitize_value():
    from app.services.sanitize import sanitize_value

    assert sanitize_value("=CMD") == "'=CMD"


def test_sanitize_value_edge_cases():
    from app.services.sanitize import sanitize_value

    assert sanitize_value("normal") == "normal"


@pytest.mark.asyncio
async def test_process_csv_sync_gridfs(mock_mongo):
    """Test the PyMongo (Sync) path where fs_bucket returns a list."""
    mock_db, mock_fs = mock_mongo
    file_id = str(ObjectId())

    # Mock DB document return
    mock_db.files.find_one.return_value = {
        "_id": ObjectId(file_id),
        "filename": "test.csv",
    }

    # Mock Sync GridFS find() returning a list of GridOut
    csv_content = b"col_a,col_b\nval_a,val_b\n"
    mock_out = MagicMock()
    mock_out.read.return_value = csv_content
    mock_fs.find.return_value = [mock_out]

    # Run
    records = await csv_processor.process_csv(file_id)

    # Assertions
    assert len(records) == 1
    assert records[0]["col_a"] == "val_a"
    assert records[0]["col_b"] == "val_b"


@pytest.mark.asyncio
async def test_process_csv_async_gridfs(mock_mongo):
    """Test the Motor (Async) path where fs_bucket returns an async cursor."""
    mock_db, mock_fs = mock_mongo
    file_id = str(ObjectId())

    # Mock DB document return
    mock_db.files.find_one.return_value = {
        "_id": ObjectId(file_id),
        "filename": "test.csv",
    }

    csv_content = b"col_a,col_b\nval_a,val_b\n"

    # Mock Async GridOut
    mock_out = MagicMock()
    # Ensure read returns bytes, awaited
    mock_out.read = AsyncMock(return_value=csv_content)

    # Mock Async Cursor
    mock_cursor = MagicMock()
    mock_cursor.to_list = AsyncMock(return_value=[mock_out])

    mock_fs.find.return_value = mock_cursor

    # Run
    records = await csv_processor.process_csv(file_id)

    assert len(records) == 1
    assert records[0]["col_a"] == "val_a"


@pytest.mark.asyncio
async def test_process_csv_with_injection(mock_mongo):
    """Test that CSV injection is sanitized."""
    mock_db, mock_fs = mock_mongo
    file_id = str(ObjectId())

    mock_db.files.find_one.return_value = {
        "_id": ObjectId(file_id),
        "filename": "injection.csv",
    }

    csv_content = b"formula,safe\n=CMD|' /C calc'!A0,normal_value\n"
    mock_out = MagicMock()
    mock_out.read.return_value = csv_content
    mock_fs.find.return_value = [mock_out]

    records = await csv_processor.process_csv(file_id)

    assert len(records) == 1
    # Check injection is sanitized
    assert records[0]["formula"].startswith("'")
    assert records[0]["safe"] == "normal_value"


@pytest.mark.asyncio
async def test_process_csv_id_field_grouping(mock_mongo):
    """Test grouping rows into records based on ID field."""
    mock_db, mock_fs = mock_mongo
    # FIX: Use a valid ObjectId hex string
    valid_id = str(ObjectId())

    mock_db.files.find_one.return_value = {
        "_id": ObjectId(valid_id),
        "filename": "grouped.csv",
    }

    csv_content = b"id,1\nname,bob\nid,2\nname,alice\n"
    mock_out = MagicMock()
    mock_out.read.return_value = csv_content
    mock_fs.find.return_value = [mock_out]

    # Run with valid_id
    records = await csv_processor.process_csv(valid_id, id_field="id")

    # Should group into 2 records
    assert len(records) == 2
