"""
CSV Handling Service.
Parses, sanitizes, and extracts schema from CSV content using dialect detection.
"""

import csv
import logging
from io import StringIO
from typing import List, Tuple, Set, Dict, Optional
from collections import OrderedDict

from fastapi.concurrency import run_in_threadpool
from app.utils.sanitize import sanitize_cell_value
from app.services.dialect_detector import DialectDetector
from app.services.transposer import parse_vertical_csv

logger = logging.getLogger(__name__)


def _is_vertical_layout(content: str, dialect: csv.Dialect) -> bool:
    """
    Heuristic to check if the file is likely a Vertical Key-Value dump.

    Signs of Vertical Layout:
    1. Most rows have exactly 2 columns (Key, Value).
    2. The first column values repeat frequently (high duplication rate).
    """
    sample_io = StringIO(content[:4096])  # Check first 4KB
    reader = csv.reader(sample_io, dialect=dialect)

    row_lengths = []
    first_col_values = []

    try:
        for _ in range(20):  # Check first 20 lines
            row = next(reader)
            if row:
                row_lengths.append(len(row))
                first_col_values.append(row[0])
    except StopIteration:
        pass
    except csv.Error:
        return False

    if not row_lengths:
        return False

    # Check 1: Are 90% of rows length 2? (Allowing for some noise)
    # Note: Your example had separator lines "---", so we should look for "Small width"
    avg_width = sum(row_lengths) / len(row_lengths)
    if avg_width > 2.5:
        return False  # Horizontal files usually have many columns

    # Check 2: Repetition. If it's a standard CSV, column 0 (ID) usually is unique.
    # If it's vertical, column 0 (Field Name) repeats every N rows.
    # If we have 20 rows and 5 unique keys, duplication is high.
    unique_keys = set(first_col_values)
    duplication_ratio = 1 - (len(unique_keys) / len(first_col_values))

    # If more than 30% of keys are duplicates, it's likely vertical
    is_vertical = duplication_ratio > 0.3

    if is_vertical:
        logger.info(
            "Vertical Key-Value layout detected (Duplication: %.2f)", duplication_ratio
        )

    return is_vertical


def _detect_dialect(content: str) -> csv.Dialect:
    """
    Helper to detect CSV dialect.
    Returns the detected dialect or falls back to 'excel'.
    """
    detector = DialectDetector()
    try:
        # Detect returns a csv.Dialect object with delimiter, quotechar, etc.
        dialect = detector.detect(content)
        logger.info(
            "Detected dialect - Delimiter: '%s', Quotechar: '%s'",
            dialect.delimiter,
            dialect.quotechar,
        )
        return dialect
    # pylint: disable=broad-exception-caught
    except Exception as error:
        logger.warning(
            "Dialect detection failed: %s. Falling back to default 'excel'.", error
        )
        return csv.get_dialect("excel")


def _parse_csv_sync(content: str) -> Tuple[List[Dict], List[str]]:
    """
    Synchronous logic to parse, sanitize, and extract schema from CSV content.
    Uses DialectDetector to handle messy CSVs (Pattern & Type scoring).
    """
    if not content:
        return [], []

    dialect = _detect_dialect(content)

    # --- ADAPTIVE STRATEGY START ---
    if _is_vertical_layout(content, dialect):
        logger.info("Delegating to Vertical Transposer...")
        return parse_vertical_csv(content, dialect)
    # --- ADAPTIVE STRATEGY END ---

    text_io = StringIO(content)
    records: List[Dict] = []
    fields_set: Set[str] = set()
    ordered_fields: List[str] = []

    try:
        # Pass the detected dialect object directly to DictReader
        reader = csv.DictReader(text_io, dialect=dialect)

        if reader.fieldnames:
            fields_set.update(reader.fieldnames)
            ordered_fields = reader.fieldnames

        for row in reader:
            sanitized_row = OrderedDict()

            for field, value in row.items():
                if field:
                    clean_field = field.strip()
                    # Safe guard for None values in case of malformed rows
                    raw_value = value if value is not None else ""
                    clean_value = sanitize_cell_value(raw_value)
                    sanitized_row[clean_field] = clean_value

            if sanitized_row:
                records.append(sanitized_row)

    except csv.Error as error:
        logger.error("CSV Parsing Error: %s", error)
        # We return what we managed to parse so far

    return records, ordered_fields


async def process_csv_content(
    content: str, id_field: Optional[str] = None
) -> Tuple[List[Dict], List[str]]:
    """
    Asynchronous wrapper for the CPU-bound CSV parsing logic.

    Args:
        content: Raw CSV string content.
        id_field: Optional ID field name (reserved for future grouping logic).
    """
    # id_field is currently unused in the parsing logic but kept for interface compatibility
    _ = id_field
    return await run_in_threadpool(_parse_csv_sync, content)
