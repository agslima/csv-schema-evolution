import csv
from app.services.sanitize import sanitize_value
from app.db.mongo import db, fs_bucket
from bson import ObjectId
import io
import inspect


async def process_csv(file_id: str, id_field: str = None):
    # Support db being either a Database (with .files) or a collection-like object (db itself)
    files_coll = getattr(db, "files", db)

    # call find_one whether it's async or sync
    find_one_fn = getattr(files_coll, "find_one")
    if inspect.iscoroutinefunction(find_one_fn):
        doc = await find_one_fn({"_id": ObjectId(file_id)})
    else:
        doc = find_one_fn({"_id": ObjectId(file_id)})

    if not doc:
        raise ValueError("File not found")

    # read file from GridFS: support both async (motor-gridfs) and sync (pymongo-gridfs) patterns
    grid_out = None
    # preferred: fs_bucket.find(...) pattern (returns cursor)
    if hasattr(fs_bucket, "find"):
        cursor = fs_bucket.find({"filename": doc["filename"]})
        # motor returns a cursor with to_list coroutine
        if hasattr(cursor, "to_list") and inspect.iscoroutinefunction(cursor.to_list):
            # async cursor
            outs = await cursor.to_list(length=1)
            grid_out = outs[0] if outs else None
        else:
            # sync cursor / iterable
            try:
                grid_out = next(iter(cursor))
            except StopIteration:
                grid_out = None
    # fallback: GridFSBucket API provides open_download_stream_by_name
    if grid_out is None and hasattr(fs_bucket, "open_download_stream_by_name"):
        stream = fs_bucket.open_download_stream_by_name(doc["filename"])
        read_fn = getattr(stream, "read", None)
        if read_fn:
            if inspect.iscoroutinefunction(read_fn):
                content = await read_fn()
            else:
                content = read_fn()
            text_io = io.StringIO(content.decode("utf-8-sig"))
        else:
            raise RuntimeError("Unable to read file stream from fs_bucket")
    else:
        if not grid_out:
            raise RuntimeError("File not found in GridFS")
        # grid_out may have either async or sync read()
        read_fn = getattr(grid_out, "read", None)
        if inspect.iscoroutinefunction(read_fn):
            content = await read_fn()
        else:
            content = read_fn()
        text_io = io.StringIO(content.decode("utf-8-sig"))

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

        if id_field and field == id_field and current_record:
            records.append(current_record)
            current_record = {}
        elif not id_field and field in current_record:
            records.append(current_record)
            current_record = {}

        current_record[field] = value

    if current_record:
        records.append(current_record)

    # update metadata in Mongo - support async or sync update_one
    update_one_fn = getattr(files_coll, "update_one")
    update_payload = {
        "$set": {
            "status": "processed",
            "fields": list(fields_set),
            "records_count": len(records),
        }
    }
    if inspect.iscoroutinefunction(update_one_fn):
        await update_one_fn({"_id": ObjectId(file_id)}, update_payload)
    else:
        update_one_fn({"_id": ObjectId(file_id)}, update_payload)

    return records
