"""
Deprecated storage helpers.
Use app.repositories.file_repository instead.
"""

import warnings
from typing import Optional, List

from bson import ObjectId
from fastapi import UploadFile

from app.repositories import file_repository

_DEPRECATION_MESSAGE = (
    "app.utils.storage is deprecated; use app.repositories.file_repository."
)


def _warn_deprecated() -> None:
    warnings.warn(_DEPRECATION_MESSAGE, DeprecationWarning, stacklevel=2)


async def save_file_to_gridfs(file: UploadFile) -> ObjectId:
    """
    Reads the file stream, encrypts it, and saves it to MongoDB GridFS.
    """
    _warn_deprecated()
    content = await file.read()
    return await file_repository.save_file(content, file.filename)


async def create_file_metadata(file_id: ObjectId, filename: str) -> dict:
    """Creates the initial metadata document in the 'files' collection."""
    _warn_deprecated()
    return await file_repository.create_file_metadata(file_id, filename)


async def get_file_content_as_string(file_id: str) -> str:
    """Retrieves file bytes from GridFS, decrypts, and decodes to string."""
    _warn_deprecated()
    return await file_repository.get_file_content_as_string(file_id)


async def update_file_status(
    file_id: str,
    status: str,
    fields: Optional[List[str]] = None,
    count: Optional[int] = 0,
    error_msg: Optional[str] = None,
) -> None:
    """
    Updates the file processing status, fields, count, and error messages.
    """
    _warn_deprecated()
    await file_repository.update_file_status(
        file_id, status, fields=fields, count=count, error_msg=error_msg
    )


async def delete_file(file_id: str) -> bool:
    """Deletes metadata and GridFS chunks."""
    _warn_deprecated()
    return await file_repository.delete_file(file_id)
