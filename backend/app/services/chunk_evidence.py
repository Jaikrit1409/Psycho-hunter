from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.document_chunk import DocumentChunk


def find_evidence_chunk(
    db: Session,
    *,
    document_id: int,
    evidence_text: str,
) -> DocumentChunk | None:
    """
    Find the document chunk containing the supplied evidence text.

    Matching is performed using normalized whitespace so that minor
    formatting differences do not prevent a match.
    """

    if not evidence_text or not evidence_text.strip():
        return None

    normalized_evidence = " ".join(evidence_text.split()).lower()

    chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index)
        .all()
    )

    for chunk in chunks:
        normalized_chunk = " ".join(chunk.content.split()).lower()

        if normalized_evidence in normalized_chunk:
            return chunk

    return None