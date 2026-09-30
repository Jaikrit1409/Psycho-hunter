from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentIngestRead(BaseModel):
    id: int
    source_id: int
    title: str | None = None
    content: str | None = None
    published_at: datetime | None = None
    collected_at: datetime | None = None
    content_hash: str | None = None

    model_config = ConfigDict(from_attributes=True)
