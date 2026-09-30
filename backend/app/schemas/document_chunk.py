from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentChunkRead(BaseModel):
    id: int
    document_id: int
    chunk_index: int
    content: str
    embedding: list[float] | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
