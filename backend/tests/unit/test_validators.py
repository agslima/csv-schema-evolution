"""
Unit tests for file validators.
"""

from io import BytesIO
import pytest
from fastapi import HTTPException, UploadFile
from app.utils.validators import validate_csv_file


def test_validate_valid_csv():
    """Test that a valid CSV passes validation."""
    # The 'content_type' property is derived automatically from these headers
    file = UploadFile(
        file=BytesIO(b"data"), filename="data.csv", headers={"content-type": "text/csv"}
    )

    # Should not raise exception
    validate_csv_file(file)


def test_validate_invalid_extension():
    """Test that non-csv extension raises error."""
    file = UploadFile(
        file=BytesIO(b"img"),
        filename="image.png",
        headers={"content-type": "image/png"},
    )

    with pytest.raises(HTTPException) as exc:
        validate_csv_file(file)

    assert exc.value.status_code == 400
    assert "Invalid file type" in exc.value.detail


def test_validate_invalid_content_type():
    """Test that valid extension but wrong content type raises error."""
    file = UploadFile(
        file=BytesIO(b"fake"),
        filename="fake.csv",
        headers={"content-type": "image/png"},
    )

    with pytest.raises(HTTPException) as exc:
        validate_csv_file(file)

    assert exc.value.status_code == 400
    assert "Invalid CSV content type" in exc.value.detail
