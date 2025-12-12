"""
Module for processing CSV files from GridFS.
Handles asynchronous and synchronous database operations.
"""

import csv
import inspect
import logging
from io import StringIO  # Fixed: Direct import avoids Pylint E1101

from bson import ObjectId
from app.utils.sanitize import sanitize_value
from app.db.mongo import db, fs_bucket

# Configure logger
logger = logging.getLogger(__name__)


async def _get_file_doc(file_id: str):
    """Retrieve file document from the database (supports sync/async)."""
    files_coll = getattr(db, "files", db)
    find_one_fn = getattr(files_coll, "find_one")

    query = {"_id": ObjectId(file_id)}

    if inspect.iscoroutinefunction(find_one_fn):
        doc = await find_one_fn(query)
    else:
        doc = find_one_fn(query)

    if not doc:
        raise ValueError("File not found")
    return doc


async def _read_content_from_gridfs(doc) -> str:
    """
    Fetch file content from GridFS, handling various bucket implementations
    (Motor vs PyMongo) and Sync vs Async streams.
    """
    filename = doc["filename"]
    read_fn = None
    grid_out = None

    # Strategy 1: fs_bucket.find()
    if hasattr(fs_bucket, "find"):
        cursor = fs_bucket.find({"filename": filename})
        if hasattr(cursor, "to_list") and inspect.iscoroutinefunction(cursor.to_list):
            outs = await cursor.to_list(length=1)
            grid_out = outs[0] if outs else None
        else:
            try:
                grid_out = next(iter(cursor))
            except StopIteration:
                grid_out = None

    # Strategy 2: open_download_stream_by_name (if Strategy 1 failed or yielded nothing)
    if grid_out is None and hasattr(fs_bucket, "open_download_stream_by_name"):
        stream = fs_bucket.open_download_stream_by_name(filename)
        read_fn = getattr(stream, "read", None)
    elif grid_out:
        read_fn = getattr(grid_out, "read", None)

    if not read_fn:
        raise RuntimeError("File not found in GridFS or unable to read stream")

    # Execute Read
    if inspect.iscoroutinefunction(read_fn):
        content = await read_fn()
    else:
        content = read_fn()

    return content.decode("utf-8-sig")


def _parse_csv_content(content: str, id_field: str | None):
    """Parse CSV content string into a list of records."""
    # Fixed: Using StringIO directly from the specific import
    text_io = StringIO(content)
    records = []
    fields_set = set()
    current_record = {}

    reader = csv.reader(text_io)
    for row in reader:
        if not row:
            continue

        field = row[0].strip()
        value = sanitize_value(row[1].strip() if len(row) > 1 else "")
        fields_set.add(field)

        # Determine if we should flush the current record
        is_new_id = id_field and field == id_field and current_record
        is_implicit_new = not id_field and field in current_record

        if is_new_id or is_implicit_new:
            records.append(current_record)
            current_record = {}

        current_record[field] = value

    if current_record:
        records.append(current_record)

    return records, fields_set


async def _update_file_status(file_id: str, fields_set: set, record_count: int):
    """Update the file status in the database (supports sync/async)."""
    files_coll = getattr(db, "files", db)
    update_one_fn = getattr(files_coll, "update_one")

    update_payload = {
        "$set": {
            "status": "processed",
            "fields": list(fields_set),
            "records_count": record_count,
        }
    }

    if inspect.iscoroutinefunction(update_one_fn):
        await update_one_fn({"_id": ObjectId(file_id)}, update_payload)
    else:
        update_one_fn({"_id": ObjectId(file_id)}, update_payload)


async def process_csv(file_id: str, id_field: str = None):
    """
    Main entry point to process a CSV file uploaded to GridFS.
    Orchestrates fetching, parsing, and updating status.
    """
    # 1. Get Document
    doc = await _get_file_doc(file_id)

    # 2. Get Content (Handles the complexity of GridFS APIs)
    content_str = await _read_content_from_gridfs(doc)

    # 3. Parse Data
    records, fields_set = _parse_csv_content(content_str, id_field)

    # 4. Update Status
    await _update_file_status(file_id, fields_set, len(records))

    return records
