"""
Unit tests for CSV processor service.
"""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from bson import ObjectId
from app.services import csv_processor


@pytest.mark.asyncio
async def test_process_csv_sync_gridfs():
    """Test the PyMongo (Sync) path."""
    file_id = str(ObjectId())

    # FIX 1: Change data to "Key,Value" format to match the parser
    # Old: b"col_a,col_b\nval_a,val_b\n" (Horizontal)
    # New: b"col_a,val_a\ncol_b,val_b\n" (Vertical Key-Value)
    csv_content = b"col_a,val_a\ncol_b,val_b\n"

    with patch("app.services.csv_processor.db") as mock_db, patch(
        "app.services.csv_processor.fs_bucket"
    ) as mock_fs:

        mock_db.files.find_one.return_value = {
            "_id": ObjectId(file_id),
            "filename": "test.csv",
        }

        mock_out = MagicMock()
        # FIX 2: Use side_effect to simulate [Content, EOF]
        mock_out.read.side_effect = [csv_content, b""]
        mock_fs.find.return_value = [mock_out]

        records = await csv_processor.process_csv(file_id)

        assert len(records) == 1
        assert records[0]["col_a"] == "val_a"
        assert records[0]["col_b"] == "val_b"


@pytest.mark.asyncio
async def test_process_csv_async_gridfs():
    """Test the Motor (Async) path."""
    file_id = str(ObjectId())
    # FIX: Key,Value format
    csv_content = b"col_a,val_a\n"

    with patch("app.services.csv_processor.db") as mock_db, patch(
        "app.services.csv_processor.fs_bucket"
    ) as mock_fs:

        mock_db.files.find_one.return_value = {
            "_id": ObjectId(file_id),
            "filename": "test.csv",
        }

        mock_out = MagicMock()
        # FIX: Async read side_effect
        mock_out.read = AsyncMock(side_effect=[csv_content, b""])

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
    # FIX: Key,Value format. Key="formula", Value="=CMD..."
    csv_content = b"formula,=CMD|' /C calc'!A0\n"

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
        # The value associated with 'formula' should be sanitized
        assert records[0]["formula"].startswith("'")
