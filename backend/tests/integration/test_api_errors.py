"""
Integration tests for API error handling.
Validates 400/404/500 scenarios for Upload, Download, and Delete.
"""

from unittest.mock import patch, AsyncMock, MagicMock
import pytest
from httpx import AsyncClient, ASGITransport
from bson import ObjectId
from app.main import app

BASE_URL = "http://test/api/v1/files"


@pytest.fixture(name="api_client")
async def fixture_api_client(mock_db_manager):
    """
    Fixture for AsyncClient.
    CRITICAL: We request 'mock_db_manager' here to ensure the DB is mocked
    before the app starts or any patches run.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test", follow_redirects=True
    ) as client:
        yield client


@pytest.mark.asyncio
async def test_upload_storage_failure(api_client):
    """Test upload endpoint when storage service fails (e.g., corrupt file)."""
    # Simulate a ValueError during GridFS save
    with patch(
        "app.utils.storage.save_file_to_gridfs",
        side_effect=ValueError("Simulated Storage Error"),
    ):
        files = {"file": ("test.csv", "col1,col2", "text/csv")}
        response = await api_client.post(f"{BASE_URL}/upload", files=files)

        # Should return 400 Bad Request with the error message
        assert response.status_code == 400
        assert "Simulated Storage Error" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_general_exception(api_client):
    """Test upload endpoint when an unexpected error occurs (500)."""
    # Simulate a generic unexpected exception
    with patch(
        "app.utils.storage.save_file_to_gridfs", side_effect=Exception("Database Down")
    ):
        files = {"file": ("test.csv", "col1,col2", "text/csv")}
        response = await api_client.post(f"{BASE_URL}/upload", files=files)

        assert response.status_code == 500
        assert "Internal Server Error" in response.json()["detail"]


@pytest.mark.asyncio
async def test_download_file_not_found(api_client, mock_db_manager):
    """Test downloading a file that does not exist in DB."""
    fake_id = str(ObjectId())

    # Configure the existing mock from the fixture
    # We don't need 'patch' here because mock_db_manager is already a mock
    mock_db_manager.db.files.find_one.return_value = None

    response = await api_client.get(f"{BASE_URL}/{fake_id}/download")
    assert response.status_code == 404
    assert "File not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_download_storage_read_error(api_client, mock_db_manager):
    """Test downloading a file where storage retrieval fails."""
    fake_id = str(ObjectId())
    mock_doc = {"_id": ObjectId(fake_id), "filename": "test.csv"}

    # 1. Setup DB Mock to find the file
    # We use AsyncMock because find_one is awaited in the endpoint
    mock_db_manager.db.files.find_one = AsyncMock(return_value=mock_doc)

    # 2. Simulate storage error (e.g. GridFS chunk missing)
    with patch(
        "app.utils.storage.get_file_content_as_string",
        side_effect=Exception("Read Error"),
    ):
        response = await api_client.get(f"{BASE_URL}/{fake_id}/download")
        assert response.status_code == 404
        assert "error reading" in response.json()["detail"]


@pytest.mark.asyncio
async def test_delete_file_not_found(api_client):
    """Test deleting a file that returns False from storage (not found)."""
    fake_id = str(ObjectId())

    # Simulate storage.delete_file returning False
    with patch("app.utils.storage.delete_file", new_callable=AsyncMock) as mock_delete:
        mock_delete.return_value = False

        response = await api_client.delete(f"{BASE_URL}/{fake_id}")
        assert response.status_code == 404
        assert "File not found" in response.json()["detail"]
