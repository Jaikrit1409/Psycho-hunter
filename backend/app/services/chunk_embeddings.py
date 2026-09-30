from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.document_chunk import DocumentChunk
from app.services.embeddings import create_embedding


def create_chunk_embedding(
    db: Session,
    *,
    chunk_id: int,
) -> DocumentChunk:
    """
    Create and store an embedding for one document chunk.

    The embedding is currently stored in the existing JSON column.
    A later migration can move this field to a native pgvector type.
    """

    chunk = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.id == chunk_id)
        .first()
    )

    if chunk is None:
        raise ValueError("Document chunk not found")

    if not chunk.content or not chunk.content.strip():
        raise ValueError("Document chunk content is empty")

    embedding = create_embedding(chunk.content)

    chunk.embedding = embedding

    db.commit()
    db.refresh(chunk)

    return chunk