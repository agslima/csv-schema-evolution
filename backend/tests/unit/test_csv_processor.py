import pytest
from app.services import csv_processor, sanitize


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
    # Single character dangerous prefix
    assert sanitize.sanitize_value("=") == "'="
    # Dangerous prefix in middle (should not be sanitized)
    assert sanitize.sanitize_value("text=value") == "text=value"
    # Multiple characters of same dangerous prefix
    assert sanitize.sanitize_value("===DANGER") == "'===DANGER"


@pytest.mark.asyncio
async def test_process_csv(tmp_path):
    """Test CSV processing with basic fields and values."""
    from unittest.mock import AsyncMock, MagicMock, patch
    from bson import ObjectId

    csv_file = tmp_path / "test.csv"
    csv_file.write_text("field1,value1\nfield2,value2\n")

    # Create a valid ObjectId for testing
    test_oid = ObjectId()
    test_oid_str = str(test_oid)

    # Create mock for fs_bucket find - simulate sync GridFS behavior
    mock_out = MagicMock()
    mock_out.read.return_value = csv_file.read_bytes()

    mock_fs_bucket = MagicMock()
    # Return a sync iterable (list) instead of async cursor
    mock_fs_bucket.find.return_value = [mock_out]

    # Mock db with async methods
    mock_db = MagicMock()
    mock_db.files = MagicMock()
    mock_db.files.find_one = AsyncMock(
        return_value={"_id": test_oid, "filename": "test.csv", "status": "pending"}
    )
    mock_db.files.update_one = AsyncMock()

    # Patch in the csv_processor module where it's imported
    with patch("app.services.csv_processor.fs_bucket", mock_fs_bucket):
        with patch("app.services.csv_processor.db", mock_db):
            records = await csv_processor.process_csv(test_oid_str)
            assert len(records) == 1
            assert records[0]["field1"] == "value1"


@pytest.mark.asyncio
async def test_process_csv_with_injection(tmp_path):
    """Test CSV processing sanitizes dangerous values."""
    from unittest.mock import AsyncMock, MagicMock, patch
    from bson import ObjectId

    csv_file = tmp_path / "injection.csv"
    csv_file.write_text("formula,=MALICIOUS()\nemail,+CMD\nname,@SYSTEM\n")

    # Create a valid ObjectId for testing
    test_oid = ObjectId()
    test_oid_str = str(test_oid)

    # Create mock for fs_bucket find - simulate sync GridFS behavior
    mock_out = MagicMock()
    mock_out.read.return_value = csv_file.read_bytes()

    mock_fs_bucket = MagicMock()
    # Return a sync iterable (list) instead of async cursor
    mock_fs_bucket.find.return_value = [mock_out]

    # Mock db with async methods
    mock_db = MagicMock()
    mock_db.files = MagicMock()
    mock_db.files.find_one = AsyncMock(
        return_value={"_id": test_oid, "filename": "injection.csv", "status": "pending"}
    )
    mock_db.files.update_one = AsyncMock()

    # Patch in the csv_processor module where it's imported
    with patch("app.services.csv_processor.fs_bucket", mock_fs_bucket):
        with patch("app.services.csv_processor.db", mock_db):
            records = await csv_processor.process_csv(test_oid_str)
            # CSV processor combines header:value pairs into a single record
            assert len(records) >= 1
            record = records[0]
            assert record["formula"] == "'=MALICIOUS()"
            assert record["email"] == "'+CMD"
            assert record["name"] == "'@SYSTEM"
