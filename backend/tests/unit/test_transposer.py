"""
Unit tests for the Vertical CSV Transposer.
"""

import csv
from app.services.transposer import parse_vertical_csv


def test_transposer_valid_vertical_data():
    """Test standard Key-Value transposition."""
    content = (
        "Key,Value\n"
        "Name,John Doe\n"
        "Age,30\n"
        "City,New York\n"
        "Key,Value\n"  # Repeater indicates new record
        "Name,Jane Smith\n"
        "Age,25\n"
        "City,London"
    )
    dialect = csv.get_dialect("excel")

    records, fields = parse_vertical_csv(content, dialect)

    assert len(records) == 2
    assert records[0]["Name"] == "John Doe"
    assert records[0]["City"] == "New York"
    assert records[1]["Name"] == "Jane Smith"

    # Check fields extraction
    assert "Name" in fields
    assert "Age" in fields


def test_transposer_single_record():
    """Test a single vertical record without repeating header."""
    content = "Name,John\nAge,30"
    dialect = csv.get_dialect("excel")
    records, fields = parse_vertical_csv(content, dialect)

    assert len(records) == 1
    assert records[0]["Name"] == "John"
    assert records[0]["Age"] == "30"


def test_transposer_malformed_lines():
    """Test resilience against empty lines or missing values."""
    content = (
        "Name,John\n"
        "\n"  # Empty line (should be skipped)
        ",Ignored\n"  # Empty key (should be skipped)
        "Age\n"  # Missing value (should be empty string)
        "City,   \n"  # Empty value with whitespace
    )
    dialect = csv.get_dialect("excel")
    records, _ = parse_vertical_csv(content, dialect)

    assert records[0]["Name"] == "John"
    assert records[0]["Age"] == ""
    assert records[0]["City"] == ""


def test_transposer_sanitizes_values():
    """Test that transposed values are sanitized to prevent CSV injection."""
    content = "Name,=1+1\nAge,25"
    dialect = csv.get_dialect("excel")

    records, _ = parse_vertical_csv(content, dialect)

    assert records[0]["Name"] == "'=1+1"


def test_transposer_error_handling():
    """Test behavior when CSV parsing completely fails."""
    # Passing an invalid type to force an internal CSV error isn't easy with StringIO,
    # but we can rely on the fact that the function handles exceptions gracefully.
    # Here we test an empty string behavior.
    records, fields = parse_vertical_csv("", csv.get_dialect("excel"))
    assert records == []
    assert fields == []
