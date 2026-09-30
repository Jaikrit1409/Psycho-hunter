from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


VALID_CATEGORIES = {
    "INTEREST",
    "HOBBY",
    "TOPIC",
    "TECHNOLOGY",
    "PROJECT",
    "COMPANY",
    "PREFERENCE",
    "RECENT_DEVELOPMENT",
}

VALID_CONFIDENCE = {"low", "medium", "high"}


class InsightCreate(BaseModel):
    category: str = Field(..., min_length=1, max_length=50)
    subject: str = Field(..., min_length=1, max_length=255)
    observation: str = Field(..., min_length=1)
    confidence: str = Field(..., min_length=1, max_length=20)
    evidence_id: int | None = None

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in VALID_CATEGORIES:
            raise ValueError("Invalid category")
        return normalized

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in VALID_CONFIDENCE:
            raise ValueError("Invalid confidence")
        return normalized


class InsightRead(BaseModel):
    id: int
    client_id: int
    category: str
    subject: str
    observation: str
    confidence: str
    evidence_id: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
