"""
CSV Data Transposition Service.
Handles vertical Key-Value pair streams in memory.
"""

import csv
import logging
from io import StringIO  # <--- Crucial Import
from typing import List, Dict, Tuple
from collections import OrderedDict

from app.utils.sanitize import sanitize_cell_value

logger = logging.getLogger(__name__)


def parse_vertical_csv(
    content: str, dialect: csv.Dialect
) -> Tuple[List[Dict], List[str]]:
    """
    Parses a 'Vertical' CSV (Key, Value) and transposes it into standard records.
    """
    text_io = StringIO(content)
    reader = csv.reader(text_io, dialect=dialect)

    fields: List[str] = []
    records: List[Dict] = []

    current_record = OrderedDict()

    try:
        for row in reader:
            if not row:
                continue

            key = row[0].strip() if row[0] else ""
            if not key:
                continue
            # If line is "Key, Value", val is Value. If just "Key", val is empty.
            raw_val = row[1] if len(row) > 1 else ""
            val = sanitize_cell_value(raw_val)

            # Logic: If we see the first field again, it's a new record
            if fields and key == fields[0] and (key in current_record):
                records.append(dict(current_record))
                current_record = OrderedDict()

            if key not in fields:
                fields.append(key)

            current_record[key] = val

        if current_record:
            records.append(dict(current_record))

        logger.info(
            "Transposition complete. Found %d detected fields and %d records.",
            len(fields),
            len(records),
        )

        return records, fields

    except csv.Error as err:
        logger.error("Error during transposition: %s", err)
        return [], []
