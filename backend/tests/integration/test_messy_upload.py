"""
Integration tests for uploading 'messy' CSV files.
Verifies dialect detection and parsing of non-standard delimiters and quotes.
"""
import pytest
from httpx import AsyncClient, ASGITransport
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
    # Note line 2: "Paris; TX" contains the delimiter inside quotes.
    csv_content = (
        "id;location;event_date;amount\n"
        "1;New York;2023-01-01;100.50\n"
        '2;"Paris; TX";2023-01-02;200.00\n'
        "3;Tokyo;2023-01-03;300.00"
    )

    # Create a file-like object for the upload
    # The filename needs to end in .csv to pass validators
    files = {"file": ("messy_data.csv", csv_content, "text/csv")}

    # 2. Perform the Request
    # We use ASGITransport to bypass the need for a running uvicorn instance
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post("/api/v1/files/upload", files=files)

    # 3. Assertions

    # Check if the request was successful
    assert response.status_code == 201, f"Upload failed: {response.text}"

    data = response.json()

    # Verify Metadata
    assert data["filename"] == "messy_data.csv"
    assert data["status"] == "processed"

    # CRITICAL: Verify correct parsing
    # If the detector failed and used comma (default), it would likely
    # see 1 column per row or fail to split "Paris; TX".

    # We expect 4 fields: id, location, event_date, amount
    expected_fields = ["id", "location", "event_date", "amount"]
    assert (
        data["fields"] == expected_fields
    ), f"Dialect detection failed. Expected {expected_fields}, got {data['fields']}"

    # We expect 3 records
    assert data["records_count"] == 3

    print("\n[SUCCESS] Messy CSV integration test passed!")
    print(f"Detected Fields: {data['fields']}")
    print(f"Records Count: {data['records_count']}")
