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

import csv
import argparse
import os
from collections import OrderedDict, Counter


def detect_delimiter(file_path):
    """Detect CSV delimiter automatically."""
    try:
        with open(file_path, "r", encoding="utf-8-sig", newline="") as csv_file:
            sample = csv_file.read(8192)
            csv_file.seek(0)
            return (
                csv.Sniffer().sniff(sample, delimiters=[",", ";", "\t", "|"]).delimiter
            )
    except (csv.Error, UnicodeDecodeError, IOError):
        # Fallback logic if Sniffer fails
        with open(file_path, "r", encoding="utf-8-sig", newline="") as csv_file:
            first_line = csv_file.readline()
        return ";" if first_line.count(";") > first_line.count(",") else ","


def read_records(input_files):
    """
    Read all records and dynamically detect new fields (schema evolution).
    Returns:
        - fields (list of str): all detected column names
        - records (list of OrderedDict): all records aligned to the final schema
        - counts (Counter): occurrences of each field name
    """
    fields = []
    records = []
    counts = Counter()

    for file_path in input_files:
        delim = detect_delimiter(file_path)
        print(f"[INFO] Processing '{file_path}' with detected delimiter '{delim}'")

        current_record = OrderedDict((c, "") for c in fields)

        with open(file_path, "r", encoding="utf-8-sig", newline="") as csv_file:
            reader = csv.reader(csv_file, delimiter=delim)
            for row in reader:
                if not row:
                    continue
                field_name = row[0].strip()
                value = row[1].strip() if len(row) > 1 else ""
                counts[field_name] += 1

                # New record detection
                if fields and field_name == fields[0] and current_record[fields[0]]:
                    records.append(current_record)
                    current_record = OrderedDict((c, "") for c in fields)

                # New field detected mid-processing
                if field_name not in fields:
                    fields.append(field_name)
                    # Add this new field to all previous records
                    for record in records:
                        record[field_name] = ""
                    current_record[field_name] = ""

                current_record[field_name] = value

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

    # Fix E1101: Pylint incorrectly flags os.path/os.makedirs in some envs
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

    Args:
        input_files (list): List of input file paths.
        output_file (str): Path to the output CSV.
        out_delim (str): Delimiter character for the output file.
        log_file (str): Path to the log file (optional).
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
