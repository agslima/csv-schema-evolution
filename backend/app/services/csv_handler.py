# backend/app/services/csv_handler.py

import csv
import logging
from io import StringIO
from typing import List, Tuple, Set, Dict, Optional
from collections import OrderedDict

from fastapi.concurrency import run_in_threadpool
from app.utils.sanitize import sanitize_cell_value
from app.services.dialect_detector import DialectDetector  # <--- NEW IMPORT

logger = logging.getLogger(__name__)


def _parse_csv_sync(
    content: str, id_field: Optional[str] = None
) -> Tuple[List[Dict], List[str]]:
    """
    Synchronous logic to parse, sanitize, and extract schema from CSV content.
    Uses DialectDetector to handle messy CSVs (Pattern & Type scoring).
    """
    if not content:
        return [], []

    # --- NEW LOGIC START ---
    # Instantiate the detector and find the best fit dialect
    detector = DialectDetector()
    try:
        # Detect returns a csv.Dialect object with delimiter, quotechar, etc.
        dialect = detector.detect(content)
        logger.info(
            "Detected dialect - Delimiter: '%s', Quotechar: '%s'",
            dialect.delimiter,
            dialect.quotechar,
        )
    except Exception as e:
        logger.warning(
            "Dialect detection failed: %s. Falling back to default 'excel'.", e
        )
        dialect = csv.get_dialect("excel")
    # --- NEW LOGIC END ---

    text_io = StringIO(content)
    records: List[Dict] = []
    fields_set: Set[str] = set()

    try:
        # Pass the detected dialect object directly to DictReader
        reader = csv.DictReader(text_io, dialect=dialect)

        if reader.fieldnames:
            fields_set.update(reader.fieldnames)
            ordered_fields = reader.fieldnames
        else:
            ordered_fields = []

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

    except csv.Error as e:
        logger.error("CSV Parsing Error: %s", e)
        # Depending on requirements, we might want to re-raise or return partial data
        # For now, we return what we managed to parse
        pass

    return records, ordered_fields


async def process_csv_content(
    content: str, id_field: Optional[str] = None
) -> Tuple[List[Dict], List[str]]:
    """
    Asynchronous wrapper for the CPU-bound CSV parsing logic.
    """
    return await run_in_threadpool(_parse_csv_sync, content, id_field)
