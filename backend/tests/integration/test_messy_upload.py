"""
Integration tests for uploading 'messy' CSV files.
Verifies dialect detection and parsing of non-standard delimiters and quotes.
"""

from unittest.mock import patch, MagicMock, AsyncMock
import pytest
from httpx import AsyncClient, ASGITransport
from bson import ObjectId
from app.main import app


# We use the ASGITransport to test the FastAPI app directly without spinning up a server
@pytest.mark.asyncio
async def test_upload_messy_csv_end_to_end():
    """
    Integration Test: Messy CSV Upload

    Scenario:
    1. A CSV file uses Semicolons (;) as delimiters (European format).
    2. One field contains the delimiter inside quotes ("Paris; France").
    3. The file has mixed types (Integers, Dates, Floats).

    Goal:
    Verify that the API automatically detects the ';' delimiter and handles
    the quoted string correctly, preserving the column count (Pattern Score).
    """

    # 1. Prepare the "Messy" CSV Content
    # Structure: ID; Location; Date; Value
    csv_content = (
        "id;location;event_date;amount\n"
        "1;New York;2023-01-01;100.50\n"
        '2;"Paris; TX";2023-01-02;200.00\n'
        "3;Tokyo;2023-01-03;300.00"
    )

    # 2. Setup Manual Mocks
    # Ensure this patch path matches your actual file structure
    with patch("app.repositories.file_repository.db_manager") as mock_db_manager:

        # Setup GridFS Mocks
        mock_fs = MagicMock()
        mock_db_manager.fs_bucket = mock_fs

        # Mock Upload Stream (Async Context Manager)
        mock_upload_stream = AsyncMock()
        # The storage service needs a valid ID to return/log.
        # pylint: disable=protected-access
        mock_upload_stream._id = ObjectId()
        mock_fs.open_upload_stream.return_value = mock_upload_stream

        # Mock Download Stream (For reading back content)
        mock_download_stream = MagicMock()
        mock_download_stream.read = AsyncMock(return_value=csv_content.encode("utf-8"))

        # Make open_download_stream an AsyncMock so it can be awaited.
        mock_fs.open_download_stream = AsyncMock(return_value=mock_download_stream)

        # Setup Standard DB Mocks (for metadata insertion)
        mock_db_manager.db.files.insert_one = AsyncMock()
        mock_db_manager.db.files.update_one = AsyncMock()

        # Create a file-like object for the upload
        files = {"file": ("messy_data.csv", csv_content, "text/csv")}

        # 3. Perform the Request
        # We also patch encryption to be a pass-through identity function
        with patch(
            "app.repositories.file_repository.encrypt_data", side_effect=lambda x: x
        ), patch(
            "app.repositories.file_repository.decrypt_data", side_effect=lambda x: x
        ):

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.post("/api/v1/files/upload", files=files)

        # 4. Assertions
        # Check if the request was successful
        assert response.status_code == 201, f"Upload failed: {response.text}"

        data = response.json()

        # Verify Metadata
        assert data["filename"] == "messy_data.csv"
        assert data["status"] == "processed"

        # CRITICAL: Verify correct parsing
        expected_fields = ["id", "location", "event_date", "amount"]
        assert (
            data["fields"] == expected_fields
        ), f"Dialect detection failed. Expected {expected_fields}, got {data['fields']}"

        # We expect 3 records
        assert data["records_count"] == 3

        # FIX: Ensure these are valid function calls
        print("\n[SUCCESS] Messy CSV integration test passed!")
        print(f"Detected Fields: {data['fields']}")
        print(f"Records Count: {data['records_count']}")
