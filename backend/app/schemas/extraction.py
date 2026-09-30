from __future__ import annotations

from pydantic import BaseModel, Field


class ExtractedInsight(BaseModel):
    category: str = Field(..., min_length=1, max_length=50)
    subject: str = Field(..., min_length=1, max_length=255)
    observation: str = Field(..., min_length=1)
    confidence: str = Field(..., min_length=1, max_length=20)
    evidence_text: str = Field(..., min_length=1)


class ExtractionResult(BaseModel):
    document_id: int
    client_id: int
    insights: list[ExtractedInsight] = Field(default_factory=list)