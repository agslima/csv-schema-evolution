"""
Repository layer for file storage and metadata operations.
Encapsulates MongoDB/GridFS access.
"""

from datetime import datetime, timezone
from typing import Optional, List, Union

from bson import ObjectId

from app.core.config import settings
from app.core.security import encrypt_data, decrypt_data
from app.db.mongo import db_manager


async def save_file(content: bytes, filename: str) -> ObjectId:
    """
    Encrypts and saves file bytes to GridFS.
    """
    if len(content) > settings.max_file_size_bytes:
        raise ValueError(f"File exceeds maximum size of {settings.MAX_FILE_SIZE_MB}MB")

    encrypted_content = encrypt_data(content)

    grid_in = db_manager.fs_bucket.open_upload_stream(filename)
    await grid_in.write(encrypted_content)
    await grid_in.close()

    # pylint: disable=protected-access
    return grid_in._id


async def save_processed_file(content: bytes, filename: str) -> ObjectId:
    """
    Encrypts and saves sanitized CSV bytes to GridFS.
    """
    processed_filename = f"processed_{filename}"
    return await save_file(content, processed_filename)


async def create_file_metadata(file_id: ObjectId, filename: str) -> dict:
    """Creates the initial metadata document in the 'files' collection."""
    file_doc = {
        "_id": file_id,
        "filename": filename,
        "raw_fs_id": file_id,
        "processed_fs_id": None,
        "status": "pending",
        "fields": [],
        "records_count": 0,
        "created_at": datetime.now(timezone.utc),
    }
    await db_manager.db.files.insert_one(file_doc)
    return file_doc


def _ensure_object_id(value: Union[str, ObjectId]) -> ObjectId:
    if isinstance(value, ObjectId):
        return value
    return ObjectId(value)


async def get_file_content_as_bytes(file_id: Union[str, ObjectId]) -> bytes:
    """Retrieves file bytes from GridFS and decrypts."""
    try:
        oid = _ensure_object_id(file_id)
        grid_out = await db_manager.fs_bucket.open_download_stream(oid)
        encrypted_content = await grid_out.read()
        return decrypt_data(encrypted_content)
    except Exception as e:
        raise ValueError(f"Could not read/decrypt file from storage: {e}") from e


async def get_file_content_as_string(file_id: Union[str, ObjectId]) -> str:
    """Retrieves file bytes from GridFS, decrypts, and decodes to string."""
    decrypted_content = await get_file_content_as_bytes(file_id)
    return decrypted_content.decode("utf-8-sig")


async def update_file_status(
    file_id: str,
    status: str,
    fields: Optional[List[str]] = None,
    count: Optional[int] = 0,
    error_msg: Optional[str] = None,
    processed_fs_id: Optional[Union[str, ObjectId]] = None,
) -> None:
    """
    Updates the file processing status, fields, count, and error messages.
    """
    update_data = {"status": status}

    if fields is not None:
        update_data["fields"] = fields
    if count is not None:
        update_data["records_count"] = count
    if error_msg:
        update_data["error_message"] = error_msg
    if processed_fs_id is not None:
        update_data["processed_fs_id"] = _ensure_object_id(processed_fs_id)

    await db_manager.db.files.update_one(
        {"_id": ObjectId(file_id)},
        {"$set": update_data},
    )


async def list_files() -> List[dict]:
    """Returns file metadata sorted by creation date (newest first)."""
    cursor = db_manager.db.files.find().sort("created_at", -1)
    results = []
    async for doc in cursor:
        results.append(doc)
    return results


async def get_file_metadata(file_id: str) -> Optional[dict]:
    """Fetches a single file metadata document by ID."""
    return await db_manager.db.files.find_one({"_id": ObjectId(file_id)})


async def delete_file(file_id: str) -> bool:
    """Deletes metadata and GridFS chunks."""
    oid = ObjectId(file_id)
    doc = await db_manager.db.files.find_one({"_id": oid})
    if not doc:
        return False

    result = await db_manager.db.files.delete_one({"_id": oid})
    if result.deleted_count == 0:
        return False

    raw_fs_id = doc.get("raw_fs_id", oid)
    await db_manager.fs_bucket.delete(_ensure_object_id(raw_fs_id))

    processed_fs_id = doc.get("processed_fs_id")
    if processed_fs_id:
        await db_manager.fs_bucket.delete(_ensure_object_id(processed_fs_id))
    return True
