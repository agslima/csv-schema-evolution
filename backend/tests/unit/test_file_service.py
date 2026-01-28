"""
Unit tests for file_service branches not covered by API tests.
"""

from unittest.mock import AsyncMock, patch
import pytest
from bson import ObjectId

from app.services import file_service


@pytest.mark.asyncio
async def test_download_processed_file_uses_cached_processed_file():
    file_id = str(ObjectId())
    processed_id = ObjectId()
    mock_doc = {
        "_id": ObjectId(file_id),
        "filename": "cached.csv",
        "processed_fs_id": processed_id,
    }

    with patch(
        "app.services.file_service.file_repository.get_file_metadata",
        new_callable=AsyncMock,
    ) as mock_meta, patch(
        "app.services.file_service.file_repository.get_file_content_as_bytes",
        new_callable=AsyncMock,
    ) as mock_bytes:
        mock_meta.return_value = mock_doc
        mock_bytes.return_value = b"col1\nval1"

        payload, filename = await file_service.download_processed_file(file_id)

    assert payload == b"col1\nval1"
    assert filename == "cached.csv"
    mock_bytes.assert_awaited_once_with(processed_id)


@pytest.mark.asyncio
async def test_download_processed_file_backfills_processed_file():
    file_id = str(ObjectId())
    processed_id = ObjectId()
    mock_doc = {"_id": ObjectId(file_id), "filename": "raw.csv"}

    with patch(
        "app.services.file_service.file_repository.get_file_metadata",
        new_callable=AsyncMock,
    ) as mock_meta, patch(
        "app.services.file_service.file_repository.get_file_content_as_string",
        new_callable=AsyncMock,
    ) as mock_raw, patch(
        "app.services.file_service.csv_handler.process_csv_content",
        new_callable=AsyncMock,
    ) as mock_process, patch(
        "app.services.file_service.file_repository.save_processed_file",
        new_callable=AsyncMock,
    ) as mock_save, patch(
        "app.services.file_service.file_repository.update_file_status",
        new_callable=AsyncMock,
    ) as mock_update:
        mock_meta.return_value = mock_doc
        mock_raw.return_value = "col1,col2\n1,2"
        mock_process.return_value = ([{"col1": "1", "col2": "2"}], ["col1", "col2"])
        mock_save.return_value = processed_id

        payload, filename = await file_service.download_processed_file(file_id)

    assert b"col1,col2" in payload
    assert b"1,2" in payload
    assert filename == "raw.csv"
    mock_save.assert_awaited_once()
    mock_update.assert_awaited_once_with(
        file_id,
        status="processed",
        updates={
            "fields": ["col1", "col2"],
            "records_count": 1,
            "processed_fs_id": processed_id,
        },
    )
