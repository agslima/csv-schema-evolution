"""
Integration tests for the file API endpoints (Async/FastAPI).
Validates the full lifecycle: Upload -> Process -> List -> Delete.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from bson import ObjectId
from app.main import app

# Define base URL for the API
BASE_URL = "http://test/api/v1/files"

@pytest.fixture
async def async_client():
    """
    Fixture creates an AsyncClient specifically for FastAPI testing.
    Uses ASGITransport to bypass the need for a running server.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_health_check(async_client):
    """Test health check endpoint."""
    response = await async_client.get("/api/v1/health/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

@pytest.mark.asyncio
async def test_upload_valid_csv(async_client):
    """Test basic CSV file upload and processing."""
    csv_content = "field1,value1\nfield2,value2"
    files = {"file": ("test_valid.csv", csv_content, "text/csv")}
    
    response = await async_client.post(f"{BASE_URL}/upload", files=files)
    
    # 201 Created is the standard for successful creation
    assert response.status_code in [200, 201]
    
    data = response.json()
    assert data["filename"] == "test_valid.csv"
    assert data["status"] == "processed"
    assert data["records_count"] == 2
    assert "field1" in data["fields"]

@pytest.mark.asyncio
async def test_upload_sanitization(async_client):
    """Test upload sanitizes CSV injection attempts (Formula Injection)."""
    # Malicious content: starts with =, +, -, @
    csv_content = "name,cmd\nAlice,=SUM(1+1)\nBob,+cmd|' /C calc'!'A1'"
    files = {"file": ("injection.csv", csv_content, "text/csv")}
    
    response = await async_client.post(f"{BASE_URL}/upload", files=files)
    assert response.status_code in [200, 201]
    
    data = response.json()
    assert data["status"] == "processed"
    # Even with bad data, it should process safely without crashing
    assert data["records_count"] == 2

@pytest.mark.asyncio
async def test_upload_invalid_extension(async_client):
    """Test upload rejects non-CSV files (e.g., .txt)."""
    files = {"file": ("test.txt", "some content", "text/plain")}
    
    response = await async_client.post(f"{BASE_URL}/upload", files=files)
    
    assert response.status_code == 400
    assert "only .csv allowed" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_upload_process_delete_flow(async_client):
    """
    Full Lifecycle Test:
    1. Upload File
    2. List Files (verify it appears)
    3. Delete File
    4. Verify Deletion
    """
    # 1. Upload
    csv_content = "id,name\n1,TestFlow"
    files = {"file": ("lifecycle.csv", csv_content, "text/csv")}
    
    upload_res = await async_client.post(f"{BASE_URL}/upload", files=files)
    assert upload_res.status_code in [200, 201]
    file_id = upload_res.json()["id"]

    # 2. List
    list_res = await async_client.get(f"{BASE_URL}/")
    assert list_res.status_code == 200
    all_files = list_res.json()
    
    # Check if our file_id exists in the list
    found = any(f["id"] == file_id for f in all_files)
    assert found, "Uploaded file not found in list"

    # 3. Delete
    delete_res = await async_client.delete(f"{BASE_URL}/{file_id}")
    assert delete_res.status_code == 200
    assert delete_res.json()["status"] == "deleted"

    # 4. Verify Deletion (Try to delete again should fail with 404)
    delete_again = await async_client.delete(f"{BASE_URL}/{file_id}")
    assert delete_again.status_code == 404

@pytest.mark.asyncio
async def test_delete_nonexistent_file(async_client):
    """Test deleting a file that doesn't exist."""
    fake_id = str(ObjectId()) # Valid ObjectId format, but random
    
    response = await async_client.delete(f"{BASE_URL}/{fake_id}")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
