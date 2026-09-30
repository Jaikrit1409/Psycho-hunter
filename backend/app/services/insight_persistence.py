from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.evidence import Evidence
from app.models.insight import Insight
from app.schemas.extraction import ExtractedInsight


def save_extracted_insight(
    db: Session,
    *,
    client_id: int,
    document_id: int,
    extracted: ExtractedInsight,
) -> Insight | None:
    """
    Persist one extracted insight together with its supporting evidence.

    If the exact same insight and evidence already exist for this document,
    return None instead of creating a duplicate.
    """

    existing = (
        db.query(Insight)
        .join(Evidence, Insight.evidence_id == Evidence.id)
        .filter(
            Insight.client_id == client_id,
            Insight.category == extracted.category,
            Insight.subject == extracted.subject,
            Insight.observation == extracted.observation,
            Evidence.document_id == document_id,
            Evidence.evidence_text == extracted.evidence_text,
        )
        .first()
    )

    if existing is not None:
        return None

    evidence = Evidence(
        client_id=client_id,
        document_id=document_id,
        claim=extracted.observation,
        evidence_text=extracted.evidence_text,
        confidence=extracted.confidence,
    )

    db.add(evidence)
    db.flush()

    insight = Insight(
        client_id=client_id,
        category=extracted.category,
        subject=extracted.subject,
        observation=extracted.observation,
        confidence=extracted.confidence,
        evidence_id=evidence.id,
    )

    db.add(insight)
    db.flush()

    return insight


def save_extracted_insights(
    db: Session,
    *,
    client_id: int,
    document_id: int,
    extracted_insights: list[ExtractedInsight],
) -> list[Insight]:
    """
    Persist multiple extracted insights and their evidence records.

    Duplicate insights are skipped.
    The caller is responsible for committing the transaction.
    """

    saved: list[Insight] = []

    for extracted in extracted_insights:
        insight = save_extracted_insight(
            db,
            client_id=client_id,
            document_id=document_id,
            extracted=extracted,
        )

        if insight is not None:
            saved.append(insight)

    return saved