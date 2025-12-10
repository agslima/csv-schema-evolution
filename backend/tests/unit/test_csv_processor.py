"""
Unit tests for CSV processor service.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bson import ObjectId
from app.services import csv_processor


@pytest.mark.asyncio
async def test_process_csv_sync_gridfs():
    """Test the PyMongo (Sync) path where fs_bucket returns a list."""
    file_id = str(ObjectId())
    csv_content = b"col_a,col_b\nval_a,val_b\n"

    # Patch locally to configure specific return values
    with patch("app.services.csv_processor.db") as mock_db, patch(
        "app.services.csv_processor.fs_bucket"
    ) as mock_fs:

        mock_db.files.find_one.return_value = {
            "_id": ObjectId(file_id),
            "filename": "test.csv",
        }

        # Mock Sync GridFS Output
        mock_out = MagicMock()
        # CRITICAL FIX: side_effect returns content once, then empty bytes (EOF)
        # This prevents the CSV parser from reading the header infinitely
        mock_out.read.side_effect = [csv_content, b""]
        mock_fs.find.return_value = [mock_out]

        # Run
        records = await csv_processor.process_csv(file_id)

        assert len(records) == 1
        assert records[0]["col_a"] == "val_a"
        assert records[0]["col_b"] == "val_b"


@pytest.mark.asyncio
async def test_process_csv_async_gridfs():
    """Test the Motor (Async) path where fs_bucket returns an async cursor."""
    file_id = str(ObjectId())
    csv_content = b"col_a,col_b\nval_a,val_b\n"

    with patch("app.services.csv_processor.db") as mock_db, patch(
        "app.services.csv_processor.fs_bucket"
    ) as mock_fs:

        mock_db.files.find_one.return_value = {
            "_id": ObjectId(file_id),
            "filename": "test.csv",
        }

        # Mock Async GridOut
        mock_out = MagicMock()
        # Async read needs side_effect for EOF
        mock_out.read = AsyncMock(side_effect=[csv_content, b""])

        # Mock Async Cursor
        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=[mock_out])
        mock_fs.find.return_value = mock_cursor

        records = await csv_processor.process_csv(file_id)

        assert len(records) == 1
        assert records[0]["col_a"] == "val_a"


@pytest.mark.asyncio
async def test_process_csv_with_injection():
    """Test that CSV injection is sanitized."""
    file_id = str(ObjectId())
    csv_content = b"formula,safe\n=CMD|' /C calc'!A0,normal_value\n"

    with patch("app.services.csv_processor.db") as mock_db, patch(
        "app.services.csv_processor.fs_bucket"
    ) as mock_fs:

        mock_db.files.find_one.return_value = {
            "_id": ObjectId(file_id),
            "filename": "injection.csv",
        }

        mock_out = MagicMock()
        mock_out.read.side_effect = [csv_content, b""]
        mock_fs.find.return_value = [mock_out]

        records = await csv_processor.process_csv(file_id)

        assert len(records) == 1
        # Check injection is sanitized
        assert records[0]["formula"].startswith("'")
