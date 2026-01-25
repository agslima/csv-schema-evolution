"""
CSV Handling Service.
Supports Adaptive Ingestion (Standard Horizontal + Vertical KV).
"""

import csv
import logging
from io import StringIO
from typing import List, Tuple, Dict, Optional
from collections import OrderedDict

from fastapi.concurrency import run_in_threadpool
from app.utils.sanitize import sanitize_cell_value
from app.services.dialect_detector import DialectDetector
from app.services.transposer import parse_vertical_csv

logger = logging.getLogger(__name__)


def _detect_dialect(content: str) -> csv.Dialect:
    """Helper to detect CSV dialect."""
    detector = DialectDetector()
    try:
        dialect = detector.detect(content)
        return dialect
    # pylint: disable=broad-exception-caught
    except Exception as error:
        logger.warning("Dialect detection failed: %s. Defaulting to Excel.", error)
        return csv.get_dialect("excel")


def _is_vertical_layout(content: str, dialect: csv.Dialect) -> bool:
    """
    Heuristic to check if the file is likely a Vertical Key-Value dump.
    """
    sample_io = StringIO(content[:4096])
    reader = csv.reader(sample_io, dialect=dialect)

    row_lengths = []
    first_col_values = []

    try:
        for _ in range(20):
            row = next(reader)
            if row:
                row_lengths.append(len(row))
                first_col_values.append(row[0])
    except (StopIteration, csv.Error):
        pass

    if not row_lengths:
        return False

    # Check 1: Average width is small (mostly Key,Value pairs)
    avg_width = sum(row_lengths) / len(row_lengths)
    if avg_width > 2.5:
        return False

    # Check 2: High duplication in first column (Keys repeating)
    unique_keys = set(first_col_values)
    duplication_ratio = 1 - (len(unique_keys) / len(first_col_values))

    return duplication_ratio > 0.3


def _group_records_by_id(records: List[Dict], id_field: Optional[str]) -> List[Dict]:
    """
    Groups records by an id field, merging rows that share the same identifier.
    """
    if not id_field:
        return records

    clean_id_field = id_field.strip()
    if not clean_id_field:
        return records

    grouped: "OrderedDict[str, OrderedDict]" = OrderedDict()
    ordered_records: List[OrderedDict] = []

    for record in records:
        record_id = record.get(clean_id_field)
        if not record_id:
            ordered_records.append(OrderedDict(record))
            continue

        if record_id not in grouped:
            grouped[record_id] = OrderedDict(record)
            ordered_records.append(grouped[record_id])
            continue

        for field, value in record.items():
            if field == clean_id_field:
                continue
            if value not in ("", None):
                grouped[record_id][field] = value

    return [dict(record) for record in ordered_records]


def _parse_csv_sync(
    content: str, id_field: Optional[str] = None
) -> Tuple[List[Dict], List[str]]:
    """
    Synchronous logic to parse, sanitize, and extract schema from CSV content.
    """
    if not content:
        return [], []

    dialect = _detect_dialect(content)

    # Adaptive Strategy
    if _is_vertical_layout(content, dialect):
        logger.info("Delegating to Vertical Transposer...")
        records, fields = parse_vertical_csv(content, dialect)
        return _group_records_by_id(records, id_field), fields

    text_io = StringIO(content)
    records: List[Dict] = []
    ordered_fields: List[str] = []

    try:
        reader = csv.DictReader(text_io, dialect=dialect)

        if reader.fieldnames:
            ordered_fields = [f.strip() for f in reader.fieldnames if f]

        for row in reader:
            sanitized_row = OrderedDict()

            for field, value in row.items():
                if field:
                    clean_field = field.strip()
                    raw_value = value if value is not None else ""
                    clean_value = sanitize_cell_value(raw_value)
                    sanitized_row[clean_field] = clean_value

            if sanitized_row:
                records.append(sanitized_row)

    except csv.Error as error:
        logger.error("CSV Parsing Error: %s", error)

    return _group_records_by_id(records, id_field), ordered_fields


async def process_csv_content(
    content: str, id_field: Optional[str] = None
) -> Tuple[List[Dict], List[str]]:
    """
    Asynchronous wrapper for the CPU-bound CSV parsing logic.
    """
    return await run_in_threadpool(_parse_csv_sync, content, id_field)
