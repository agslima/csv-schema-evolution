"""
Utility functions for file validation.
"""

from fastapi import HTTPException, UploadFile

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


def validate_csv_file(file: UploadFile):
    """
    Validate that the uploaded file is a CSV.

    Args:
        file (UploadFile): The file object to validate.

    Raises:
        HTTPException: If the file extension or content type is invalid.
    """
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400, detail="Invalid file type. Only CSV allowed."
        )
    content_type = (file.content_type or "").lower()
    if not (
        content_type.startswith("text/csv")
        or content_type == "application/vnd.ms-excel"
    ):
        raise HTTPException(status_code=400, detail="Invalid CSV content type.")
    # size check will be done after reading file bytes in memory
