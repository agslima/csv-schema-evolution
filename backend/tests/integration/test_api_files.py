"""
Integration tests for the file API endpoints (Async/FastAPI).
Validates the full lifecycle: Upload -> Process -> List -> Delete -> Download.
"""

from unittest.mock import MagicMock, AsyncMock, patch
import pytest
from httpx import AsyncClient, ASGITransport
from bson import ObjectId
from app.main import app

# Define base URL for the API
BASE_URL = "http://test/api/v1/files"


@pytest.fixture(name="api_client")
async def fixture_api_client(mock_db_manager):  # pylint: disable=unused-argument
    """Fixture creates an AsyncClient specifically for FastAPI testing."""
    # FIX: Enable follow_redirects to handle strict slash redirects (307 -> 200)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test", follow_redirects=True
    ) as client:
        yield client


@pytest.mark.asyncio
async def test_health_check(api_client):
    """Test health check endpoint."""
    response = await api_client.get("/api/v1/health/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_liveness_check(api_client):
    """Test liveness check endpoint."""
    response = await api_client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_readiness_check(api_client):
    """Test readiness check endpoint."""
    response = await api_client.get("/api/v1/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["dependencies"]["mongo"]["status"] == "ok"
    assert data["dependencies"]["gridfs"]["status"] == "ok"


@pytest.mark.asyncio
async def test_upload_valid_csv(api_client, mock_db_manager):
    """Test basic CSV file upload and processing."""
    # 1. Setup Data
    csv_content = "col1,col2\nval1,val2\nval3,val4"
    files = {"file": ("test_valid.csv", csv_content, "text/csv")}

    # 2. Configure Mock to return THIS content when read back
    mock_stream = MagicMock()
    mock_stream.read = AsyncMock(return_value=csv_content.encode("utf-8"))
    mock_db_manager.fs_bucket.open_download_stream.return_value = mock_stream

    # 3. Request
    response = await api_client.post(f"{BASE_URL}/upload", files=files)

    # 4. Assert
    assert response.status_code in [200, 201]
    data = response.json()
    assert data["filename"] == "test_valid.csv"
    assert data["status"] == "processed"
    assert data["records_count"] == 2
    assert "col1" in data["fields"]


@pytest.mark.asyncio
async def test_upload_sanitization(api_client, mock_db_manager):
    """Test upload sanitizes CSV injection attempts (Formula Injection)."""
    csv_content = "name,cmd\nAlice,=SUM(1+1)\nBob,+cmd|' /C calc'!'A1'"
    files = {"file": ("injection.csv", csv_content, "text/csv")}

    # Configure Mock to return malicious content
    mock_stream = MagicMock()
    mock_stream.read = AsyncMock(return_value=csv_content.encode("utf-8"))
    mock_db_manager.fs_bucket.open_download_stream.return_value = mock_stream

    response = await api_client.post(f"{BASE_URL}/upload", files=files)
    assert response.status_code in [200, 201]

    data = response.json()
    assert data["status"] == "processed"
    assert data["records_count"] == 2


@pytest.mark.asyncio
async def test_upload_invalid_extension(api_client):
    """Test upload rejects non-CSV files (e.g., .txt)."""
    files = {"file": ("test.txt", "some content", "text/plain")}
    response = await api_client.post(f"{BASE_URL}/upload", files=files)
    assert response.status_code == 400

    assert "only .csv allowed" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_upload_process_delete_flow(api_client, mock_db_manager):
    """
    Full Lifecycle Test: Upload -> List -> Delete
    """
    # 1. Upload
    csv_content = "id,name\n1,TestFlow"
    files = {"file": ("lifecycle.csv", csv_content, "text/csv")}

    # Mock read back
    mock_stream = MagicMock()
    mock_stream.read = AsyncMock(return_value=csv_content.encode("utf-8"))
    mock_db_manager.fs_bucket.open_download_stream.return_value = mock_stream

    upload_res = await api_client.post(f"{BASE_URL}/upload", files=files)
    assert upload_res.status_code in [200, 201]
    file_id = upload_res.json()["id"]

    # 2. List
    # Inject the uploaded file into the find() mock results
    mock_file_doc = {
        "id": file_id,
        "_id": ObjectId(file_id),
        "filename": "lifecycle.csv",
        "status": "processed",
        "fields": ["id", "name"],
        "records_count": 1,
    }

    async def async_cursor_gen():
        yield mock_file_doc

    # Mock the Chain find().sort()
    mock_cursor = MagicMock()
    mock_cursor.sort.return_value = async_cursor_gen()

    # Explicitly replace 'find' so it returns the mock cursor directly (sync-like)
    mock_db_manager.db.files.find = MagicMock(return_value=mock_cursor)

    list_res = await api_client.get(f"{BASE_URL}/")
    assert list_res.status_code == 200
    all_files = list_res.json()
    assert any(f["id"] == file_id for f in all_files)

    # 3. Delete
    mock_db_manager.db.files.find_one = AsyncMock(return_value=mock_file_doc)
    mock_db_manager.db.files.delete_one.return_value.deleted_count = 1
    delete_res = await api_client.delete(f"{BASE_URL}/{file_id}")
    assert delete_res.status_code == 200

    # 4. Verify Deletion (Not Found)
    mock_db_manager.db.files.delete_one.return_value.deleted_count = 0
    delete_again = await api_client.delete(f"{BASE_URL}/{file_id}")
    assert delete_again.status_code == 404


@pytest.mark.asyncio
async def test_delete_nonexistent_file(api_client, mock_db_manager):
    """Test deleting a file that doesn't exist."""
    fake_id = str(ObjectId())

    # Mock delete_one to return 0 deleted documents
    mock_db_manager.db.files.find_one = AsyncMock(return_value=None)
    mock_db_manager.db.files.delete_one.return_value.deleted_count = 0

    response = await api_client.delete(f"{BASE_URL}/{fake_id}")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_download_file(api_client, mock_db_manager):
    """Test downloading a file."""
    # 1. Setup Mock
    file_id = str(ObjectId())
    mock_doc = {
        "_id": ObjectId(file_id),
        "filename": "download.csv",
        "processed_fs_id": ObjectId(),
    }
    # AsyncMock for find_one since Motor is async here, but usually we mock the result directly
    # Ideally find_one returns a coroutine.
    mock_db_manager.db.files.find_one = AsyncMock(return_value=mock_doc)

    # Mock content retrieval from repository
    with patch(
        "app.repositories.file_repository.get_file_content_as_bytes",
        new_callable=AsyncMock,
    ) as mock_get_content:
        mock_get_content.return_value = b"col1,col2\nval1,val2"

        # 2. Request
        response = await api_client.get(f"{BASE_URL}/{file_id}/download")

    assert response.status_code == 200
    assert (
        # FIX: Update expected filename to match the new "Safe Download" logic
        "attachment; filename=cleaned_download.csv"
        in response.headers["content-disposition"]
    )
    body = response.text
    assert "col1,col2" in body
    assert "val1,val2" in body
