"""
CSV Data Transposition and Evolution Module.

This module reads multiple CSV files containing Key-Value pairs, detects new
fields dynamically (schema evolution), and outputs a transposed CSV where
keys become columns and files become rows.
"""

# ***************************************************************************
# * *
# * CSV Data Transposition and Evolution                                  *
# * *
# * This program is free software; you can redistribute it and/or modify  *
# * it under the terms of the GNU General Public License as published by  *
# * the Free Software Foundation; either version 2 of the License, or     *
# * (at your option) any later version.                                   *
# * *
# ***************************************************************************

# csv_schema_evolution.py

import csv

# ... [Other imports] ...
from app.services.dialect_detector import DialectDetector

# DELETE the old detect_delimiter function
# def detect_delimiter(file_path): ...


def read_records(input_files):
    """
    Read all records and dynamically detect new fields.
    """
    fields = []
    records = []
    counts = Counter()

    # Initialize the detector
    detector = DialectDetector()

    for file_path in input_files:
        # 1. Read a sample for detection
        try:
            with open(file_path, "r", encoding="utf-8-sig") as f:
                sample = f.read(8192)

            # 2. Detect dialect
            dialect = detector.detect(sample)
            delim = dialect.delimiter
            quote = dialect.quotechar
            print(
                f"[INFO] Processing '{file_path}' detected: Delim='{delim}', Quote='{quote}'"
            )

        except Exception as e:
            print(
                f"[WARN] Failed to detect dialect for {file_path}, defaulting to comma. Error: {e}"
            )
            delim = ","
            quote = '"'

        current_record = OrderedDict((c, "") for c in fields)

        with open(file_path, "r", encoding="utf-8-sig", newline="") as csv_file:
            # 3. Use detected dialect
            reader = csv.reader(csv_file, delimiter=delim, quotechar=quote)

            for row in reader:
                # ... [Your existing logic remains exactly the same] ...
                pass

    return fields, records, counts
