from pydantic import BaseModel
from typing import List


class FileResponse(BaseModel):
    id: str
    filename: str
    status: str
    records_count: int = 0
    fields: List[str] = []
