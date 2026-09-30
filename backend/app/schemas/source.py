from __future__ import annotations

from datetime import datetime

from pydantic import AnyUrl, BaseModel, ConfigDict, Field


class SourceCreate(BaseModel):
    url: AnyUrl
    source_type: str = Field(..., min_length=1, max_length=100)
    title: str | None = Field(default=None, max_length=255)
    publisher: str | None = Field(default=None, max_length=255)


class SourceRead(BaseModel):
    id: int
    client_id: int
    url: AnyUrl
    source_type: str | None = None
    title: str | None = None
    publisher: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
