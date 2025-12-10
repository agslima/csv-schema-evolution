import io
from app.db.mongo import db, fs_bucket
from bson import ObjectId


async def save_file(file):
    content = await file.read()
    from app.utils.validators import MAX_FILE_SIZE

    if len(content) > MAX_FILE_SIZE:
        raise ValueError("File exceeds maximum size of 50MB")

    grid_in = fs_bucket.open_upload_stream(file.filename)
    grid_in.write(content)
    grid_in.close()

    # save metadata
    file_doc = {
        "filename": file.filename,
        "status": "pending",
        "size": len(content),
        "fields": [],
        "records_count": 0,
    }
    result = await db.files.insert_one(file_doc)
    return result.inserted_id


async def get_file_stream(file_id: str):
    doc = await db.files.find_one({"_id": ObjectId(file_id)})
    if not doc:
        return None
    cursor = fs_bucket.open_download_stream_by_name(doc["filename"])
    return cursor, doc


async def delete_file(file_id: str):
    doc = await db.files.find_one({"_id": ObjectId(file_id)})
    if not doc:
        return False
    await db.files.delete_one({"_id": ObjectId(file_id)})
    # delete from GridFS
    for f in fs_bucket.find({"filename": doc["filename"]}):
        fs_bucket.delete(f._id)
    return True
