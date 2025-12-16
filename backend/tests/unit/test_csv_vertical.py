"""
Tests for the Vertical Layout Detection Heuristic in CSV Handler.
"""

import csv
from unittest.mock import patch
from app.services.csv_handler import _is_vertical_layout, _parse_csv_sync


def test_detect_vertical_layout_positive():
    """Test that the heuristic correctly identifies a vertical KV file."""
    # A file with repeating keys in col 0 and short row lengths
    content = (
        "Key,Value\n"
        "Browser,Chrome\n"
        "IP,127.0.0.1\n"
        "OS,Windows\n"
        "Key,Value\n"  # Repeater
        "Browser,Firefox\n"
        "IP,192.168.0.1\n"
        "OS,Linux\n"
    )
    dialect = csv.get_dialect("excel")
    assert _is_vertical_layout(content, dialect) is True


def test_detect_vertical_layout_negative():
    """Test that a standard horizontal CSV is NOT flagged as vertical."""
    content = "Name,Age,City,Country\nJohn,30,NY,USA\nJane,25,LDN,UK"
    dialect = csv.get_dialect("excel")
    assert _is_vertical_layout(content, dialect) is False


def test_detect_vertical_layout_wide_rows():
    """Test fail condition: Average width > 2.5."""
    # 3 columns means it's likely not a K,V pair list
    content = "K,V,Extra\nA,1,x\nB,2,y"
    dialect = csv.get_dialect("excel")
    assert _is_vertical_layout(content, dialect) is False


def test_handler_delegates_to_transposer():
    """Integration: Ensure _parse_csv_sync calls the transposer."""
    content = "Key,Value\nA,1\nKey,Value\nA,2"

    # We spy on the transposer to ensure it was actually called
    with patch("app.services.csv_handler.parse_vertical_csv") as mock_transpose:
        mock_transpose.return_value = ([{"A": "1"}, {"A": "2"}], ["A"])

        records, fields = _parse_csv_sync(content)

        mock_transpose.assert_called_once()
        assert len(records) == 2
