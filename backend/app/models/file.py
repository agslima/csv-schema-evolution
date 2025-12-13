"""
Pydantic models for file responses.
"""

from typing import List
from pydantic import BaseModel


class FileResponse(BaseModel):
    """Schema for file upload and status responses."""

    id: str
    filename: str
    status: str
    records_count: int = 0
    fields: List[str] = []
