"""
Unit tests specifically targeting edge cases and error handling branches
to achieve 100% code coverage.
"""

import csv
from io import BytesIO
from unittest.mock import patch

import pytest
from fastapi import UploadFile

from app.services.csv_handler import (
    _parse_csv_sync,
    _detect_dialect,
    process_csv_content,
)
from app.services.dialect_detector import DialectDetector
from app.utils.storage import save_file_to_gridfs

# --- 1. CSV Handler Edge Cases ---


def test_handler_empty_content():
    """Hits: if not content: return [], []"""
    records, fields = _parse_csv_sync("")
    assert not records
    assert not fields


def test_handler_dialect_detection_failure():
    """Hits: except Exception as error (fallback to excel)"""
    with patch(
        "app.services.csv_handler.DialectDetector.detect", side_effect=Exception("Boom")
    ):
        # Should not raise, but log warning and use Excel
        dialect = _detect_dialect("col1,col2\nval1,val2")
        assert dialect.delimiter == ","  # Excel default


def test_handler_csv_error_during_parsing():
    """Hits: except csv.Error as error"""
    # Create a content that looks valid
    content = "col1,col2\nval1,val2"

    # Mock DictReader to raise error during iteration
    with patch("csv.DictReader") as mock_reader:
        instance = mock_reader.return_value
        instance.fieldnames = ["col1", "col2"]
        # Simulate normal iteration then crash
        instance.__iter__.side_effect = csv.Error("Corrupt row")

        records, fields = _parse_csv_sync(content)

        # It should catch the error and return empty or partial records
        assert not records
        assert fields == ["col1", "col2"]


def test_handler_malformed_rows():
    """Hits: if field: check and None value safeguards"""
    # Manually construct a row that DictReader might yield for bad data
    # Row with None key (extra field) and None value
    bad_row = {None: ["extra"], "col1": None, "col2": " val "}

    with patch("csv.DictReader") as mock_reader:
        instance = mock_reader.return_value
        instance.fieldnames = ["col1", "col2"]
        instance.__iter__.return_value = [bad_row]

        records, _ = _parse_csv_sync("dummy")

        # 'None' key should be skipped.
        # 'None' value should become ""
        assert "col1" in records[0]
        assert records[0]["col1"] == ""

        # FIX: Expect whitespace to remain; app logic only sanitizes,
        # it does not strip values.
        assert records[0]["col2"] == " val "


@pytest.mark.asyncio
async def test_process_csv_content_async_wrapper():
    """Hits: process_csv_content async wrapper"""
    # Simply verify the async wrapper calls the sync function
    res = await process_csv_content("id,name\n1,test")
    assert len(res[0]) == 1
    assert res[0][0]["name"] == "test"


# --- 2. Dialect Detector Edge Cases ---


def test_detector_candidate_exception():
    """Hits: except Exception (inside loop)"""
    detector = DialectDetector()

    # Patch _calculate_pattern_score to raise error for one candidate
    with patch.object(
        detector, "_calculate_pattern_score", side_effect=ValueError("Math error")
    ):
        # Should catch exception and continue to next candidate/fallback
        dialect = detector.detect("col1|col2\nval1|val2")
        # Should fallback to Excel (comma) since pipe failed
        assert dialect.delimiter == ","


def test_detector_registration_error():
    """Hits: except csv.Error (inside register_dialect)"""
    detector = DialectDetector()

    # Force find a dialect
    with patch.object(detector, "_get_potential_dialects", return_value=[(",", '"')]):
        # Mock register_dialect to fail (e.g., name already exists)
        with patch("csv.register_dialect", side_effect=csv.Error("Exists")):
            # Should catch error and proceed
            dialect = detector.detect("a,b\n1,2")
            assert dialect.delimiter == ","


def test_detector_strict_parsing_error():
    """Hits: except csv.Error (inside _parse_sample)"""
    detector = DialectDetector()
    # Unclosed quote causes csv.Error when strict=True
    bad_sample = 'col1,col2\n"unclosed, value'

    # pylint: disable=protected-access
    rows = detector._parse_sample(bad_sample, ",", '"')
    assert not rows  # Should return empty list on error


def test_detector_empty_cells_score():
    """Hits: if total_cells == 0"""
    detector = DialectDetector()
    # Rows exist but have no cells (empty list of lists)
    # pylint: disable=protected-access
    score = detector._calculate_type_score([[], []])
    assert score == detector.BETA


# --- 3. Storage Edge Cases ---


@pytest.mark.asyncio
async def test_storage_max_size_exceeded():
    """Hits: if len(content) > settings.max_file_size_bytes"""
    # Create a small file
    file = UploadFile(file=BytesIO(b"12345"), filename="test.txt")

    # FIX: Patch the 'settings' object imported in app.utils.storage
    # This bypasses Pydantic property restrictions entirely
    with patch("app.utils.storage.settings") as mock_settings:
        # Set the mock to have a tiny max size
        mock_settings.max_file_size_bytes = 1

        with pytest.raises(ValueError) as exc:
            # We explicitly await the function using the file variable
            await save_file_to_gridfs(file)

        assert "exceeds maximum size" in str(exc.value)


# --- 4. Final 1% Coverage Strikes ---


def test_detector_pattern_score_direct_call():
    """
    Hits: if not rows: return 0.0 in _calculate_pattern_score.
    This is unreachable in normal flow because 'detect' filters empty rows first.
    """
    detector = DialectDetector()
    # Call the private method directly with empty list
    # pylint: disable=protected-access
    score = detector._calculate_pattern_score([])
    assert score == 0.0


def test_handler_no_fieldnames_branch():
    """
    Hits: if reader.fieldnames (False branch) and skip loop.
    Simulates a DictReader that fails to parse any headers even if content exists.
    """
    with patch("csv.DictReader") as mock_reader:
        instance = mock_reader.return_value
        # Force fieldnames to be None to hit the 'else' or skip branch
        instance.fieldnames = None
        # Force iterator to be empty to skip the 'for row in reader' loop
        instance.__iter__.return_value = []

        # Pass non-empty content so it bypasses the first check
        records, _ = _parse_csv_sync("some_content")

        assert not records
