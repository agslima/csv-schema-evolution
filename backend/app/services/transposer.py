"""
CSV Data Transposition Service.
Adapted to handle vertical Key-Value pair streams in memory.
"""

import csv
import logging
from io import StringIO
from typing import List, Dict, Tuple
from collections import OrderedDict

logger = logging.getLogger(__name__)


def parse_vertical_csv(
    content: str, dialect: csv.Dialect
) -> Tuple[List[Dict], List[str]]:
    """
    Parses a 'Vertical' CSV (Key, Value) and transposes it into standard records.

    Logic:
    - Reads line by line.
    - If a key repeats the 'first detected key' of the current record,
      it assumes a new record has started.
    - Dynamically adds new fields (Schema Evolution) if they appear mid-stream.
    """

    text_io = StringIO(content)
    reader = csv.reader(text_io, dialect=dialect)

    fields: List[str] = []
    records: List[Dict] = []

    # Initialize the first record container
    current_record = OrderedDict()

    try:
        for row in reader:
            if not row:
                continue

            # Basic validation: We expect at least a Key. Value is optional.
            key = row[0].strip()
            # If there's a second column, use it. If not, empty string.
            val = row[1].strip() if len(row) > 1 else ""

            # 1. New Record Detection
            # If we see the 'primary key' (the first field we ever found) again,
            # and our current record already has a value for it, this must be a new record.
            if fields and key == fields[0] and (key in current_record):
                # Save the completed record
                records.append(dict(current_record))
                # Reset for the next one
                current_record = OrderedDict()

            # 2. Schema Evolution (New Field Detection)
            if key not in fields:
                fields.append(key)
                # Note: In a strict DB scenario, we might need to backfill
                # previous records with None, but for JSON output, it's fine.

            # 3. Assign Value
            current_record[key] = val

        # Don't forget the last record in the buffer!
        if current_record:
            records.append(dict(current_record))

        logger.info(
            "Transposition complete. Found %d detected fields and %d records.",
            len(fields),
            len(records),
        )

        return records, fields

    except csv.Error as e:
        logger.error("Error during transposition: %s", e)
        return [], []
