"""
CSV Data Transposition and Evolution Module.

This module reads multiple CSV files containing Key-Value pairs, detects new
fields dynamically (schema evolution), and outputs a transposed CSV where
keys become columns and files become rows.
"""

import csv
import argparse
import os
from collections import OrderedDict, Counter
from app.services.dialect_detector import DialectDetector


def _get_dialect(file_path, detector):
    """
    Helper to detect dialect for a single file.
    Returns delimiter and quotechar.
    """
    try:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            sample = f.read(8192)
        dialect = detector.detect(sample)
        return dialect.delimiter, dialect.quotechar
    except (OSError, csv.Error) as e:
        print(
            f"[WARN] Failed to detect dialect for {file_path}, defaulting to comma. Error: {e}"
        )
        return ",", '"'


def read_records(input_files):
    """
    Read all records and dynamically detect new fields.
    Returns:
        - fields (list of str): all detected column names
        - records (list of OrderedDict): all records aligned to the final schema
        - counts (Counter): occurrences of each field name
    """
    fields = []
    records = []
    counts = Counter()

    # Initialize the detector
    detector = DialectDetector()

    for file_path in input_files:
        delim, quote = _get_dialect(file_path, detector)
        print(
            f"[INFO] Processing '{file_path}' detected: Delim='{delim}', Quote='{quote}'"
        )

        current_record = OrderedDict((c, "") for c in fields)

        with open(file_path, "r", encoding="utf-8-sig", newline="") as csv_file:
            reader = csv.reader(csv_file, delimiter=delim, quotechar=quote)

            for row in reader:
                if not row:
                    continue
                field_name = row[0].strip()
                value = row[1].strip() if len(row) > 1 else ""
                counts[field_name] += 1

                # New record detection (if key repeats first field)
                if fields and field_name == fields[0] and current_record[fields[0]]:
                    records.append(current_record)
                    current_record = OrderedDict((c, "") for c in fields)

                # New field detected mid-processing (Schema Evolution)
                if field_name not in fields:
                    fields.append(field_name)
                    # Backfill this new field in previous records
                    for record in records:
                        record[field_name] = ""
                    current_record[field_name] = ""

                current_record[field_name] = value

        # Append the last record of the file
        if any(v != "" for v in current_record.values()):
            records.append(current_record)

    return fields, records, counts


def write_csv(output_file, fields, records, out_delim):
    """Write transposed CSV with updated schema."""
    with open(output_file, "w", encoding="utf-8", newline="") as csv_file:
        writer = csv.writer(csv_file, delimiter=out_delim)
        writer.writerow(fields)
        for record in records:
            writer.writerow([record.get(c, "") for c in fields])


def write_log(log_file_path, counts):
    """Write CSV log of field occurrence counts."""
    if not log_file_path:
        return

    # pylint: disable=no-member
    directory = os.path.dirname(log_file_path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    with open(log_file_path, "w", encoding="utf-8", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["field", "occurrences"])
        for field, count in counts.most_common():
            writer.writerow([field, count])


def process_files(input_files, output_file, out_delim, log_file):
    """
    Orchestrate the reading, processing, and writing of CSV data.
    """
    fields, records, counts = read_records(input_files)
    write_csv(output_file, fields, records, out_delim)
    write_log(log_file, counts)
    print(f"Output file created: {output_file}")
    if log_file:
        print(f"Field occurrence log saved: {log_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="CSV transposer with schema evolution (dynamic fields)."
    )
    parser.add_argument(
        "inputs", nargs="+", help="One or more input CSV files (key,value format)."
    )
    parser.add_argument("-o", "--out", required=True, help="Output CSV file.")
    parser.add_argument(
        "--out-delim", default=",", help="Output CSV delimiter (default: ',')."
    )
    parser.add_argument("--log", help="Optional CSV file for field occurrence log.")
    arguments = parser.parse_args()

    process_files(arguments.inputs, arguments.out, arguments.out_delim, arguments.log)
