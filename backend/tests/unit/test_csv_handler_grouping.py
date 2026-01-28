"""
Unit tests for record grouping in the CSV handler.
"""

from app.services.csv_handler import _group_records_by_id


def test_group_records_by_id_without_id_field_returns_input():
    records = [{"id": "1", "name": "Alice"}, {"id": "1", "name": "Alicia"}]

    assert _group_records_by_id(records, None) == records
    assert _group_records_by_id(records, "   ") == records


def test_group_records_by_id_merges_records_and_preserves_order():
    records = [
        {"id": "1", "name": "Alice", "age": "30", "city": "NY"},
        {"id": "1", "age": "31", "city": ""},
        {"id": "2", "name": "Bob"},
        {"id": "", "name": "NoId"},
        {"name": "MissingId"},
    ]

    grouped = _group_records_by_id(records, " id ")

    assert len(grouped) == 4

    first = grouped[0]
    assert first["id"] == "1"
    assert first["name"] == "Alice"
    assert first["age"] == "31"
    assert first["city"] == "NY"

    assert grouped[1]["id"] == "2"
    assert grouped[2]["id"] == ""
    assert "id" not in grouped[3]
