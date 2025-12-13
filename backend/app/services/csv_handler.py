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

logger = logging.getLogger(__name__)


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
