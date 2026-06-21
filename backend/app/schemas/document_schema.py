from datetime import datetime
from pydantic import BaseModel

class DocumentResponse(BaseModel):
    id: str
    title: str
    filename: str
    status: str
    page_count: int | None
    created_at: datetime

class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
