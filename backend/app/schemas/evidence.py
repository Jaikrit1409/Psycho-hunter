from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EvidenceRead(BaseModel):
    id: int
    client_id: int
    document_id: int
    claim: str
    evidence_text: str
    confidence: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)