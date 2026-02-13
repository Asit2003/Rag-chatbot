from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: str
    original_name: str
    file_type: str
    size_bytes: int
    chunk_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class BatchUploadResult(BaseModel):
    indexed: list[DocumentOut]
    failed: list[dict[str, str]]
