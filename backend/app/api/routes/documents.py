from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.source import Source
from app.schemas.document_chunk import DocumentChunkRead
from app.schemas.extraction import ExtractionResult
from app.services.chunk_evidence import find_evidence_chunk
from app.services.chunking import chunk_text
from app.services.extraction import extract_insights_from_text
from app.services.insight_persistence import save_extracted_insights

router = APIRouter(tags=["documents"])


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/documents/{document_id}/chunk",
    response_model=list[DocumentChunkRead],
    status_code=status.HTTP_201_CREATED,
)
def create_document_chunks(
    document_id: int,
    db: Session = Depends(get_db),
) -> list[DocumentChunk]:
    document = (
        db.query(Document)
        .filter(Document.id == document_id)
        .first()
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    existing_chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index)
        .all()
    )

    if existing_chunks:
        return existing_chunks

    if not document.content or not document.content.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Document content is empty",
        )

    chunks = chunk_text(
        document.content,
        chunk_size=1000,
        overlap=150,
    )

    saved_chunks: list[DocumentChunk] = []

    for idx, piece in enumerate(chunks):
        chunk = DocumentChunk(
            document_id=document_id,
            chunk_index=idx,
            content=piece,
            embedding=None,
        )

        db.add(chunk)
        saved_chunks.append(chunk)

    db.commit()

    for chunk in saved_chunks:
        db.refresh(chunk)

    return saved_chunks


@router.get(
    "/documents/{document_id}/chunks",
    response_model=list[DocumentChunkRead],
)
def list_document_chunks(
    document_id: int,
    db: Session = Depends(get_db),
) -> list[DocumentChunk]:
    document = (
        db.query(Document)
        .filter(Document.id == document_id)
        .first()
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index)
        .all()
    )


@router.post(
    "/documents/{document_id}/extract",
    response_model=ExtractionResult,
    status_code=status.HTTP_200_OK,
)
def extract_document_insights(
    document_id: int,
    db: Session = Depends(get_db),
) -> ExtractionResult:
    document = (
        db.query(Document)
        .filter(Document.id == document_id)
        .first()
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    if not document.content or not document.content.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Document content is empty",
        )

    source = (
        db.query(Source)
        .filter(Source.id == document.source_id)
        .first()
    )

    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document source not found",
        )

    client_id = source.client_id

    try:
        # Make sure document chunks exist.
        existing_chunks = (
            db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index)
            .all()
        )

        if not existing_chunks:
            chunks = chunk_text(
                document.content,
                chunk_size=1000,
                overlap=150,
            )

            for idx, piece in enumerate(chunks):
                chunk = DocumentChunk(
                    document_id=document_id,
                    chunk_index=idx,
                    content=piece,
                    embedding=None,
                )

                db.add(chunk)

            db.flush()

        # Extract explicitly supported insights from the document.
        extracted_insights = extract_insights_from_text(
            document.content
        )

        # Confirm which chunks support the extracted evidence.
        for extracted in extracted_insights:
            find_evidence_chunk(
                db,
                document_id=document_id,
                evidence_text=extracted.evidence_text,
            )

        # Persist insights and supporting evidence.
        save_extracted_insights(
            db,
            client_id=client_id,
            document_id=document_id,
            extracted_insights=extracted_insights,
        )

        db.commit()

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to extract document insights",
        )

    return ExtractionResult(
        document_id=document_id,
        client_id=client_id,
        insights=extracted_insights,
    )