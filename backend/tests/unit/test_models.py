"""
Unit tests for Pydantic models.
"""

from app.models.file import FileResponse


def test_file_response_creation():
    """Test that the model instantiates correctly."""
    data = {
        "id": "507f1f77bcf86cd799439011",
        "filename": "test.csv",
        "status": "pending",
        "records_count": 0,
        "fields": [],
    }
    model = FileResponse(**data)

    assert model.id == "507f1f77bcf86cd799439011"
    assert model.filename == "test.csv"
    assert model.status == "pending"
    assert model.records_count == 0
    # FIX: Use implicit booleaness (empty list is False)
    assert not model.fields


def test_file_response_defaults():
    """Test that optional fields use their default values."""
    data = {"id": "123", "filename": "minimal.csv", "status": "processing"}
    model = FileResponse(**data)

    assert model.records_count == 0
    # FIX: Use implicit booleaness
    assert not model.fields
