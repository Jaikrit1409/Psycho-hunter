from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.schemas.document_chunk import DocumentChunkRead
from app.services.chunking import chunk_text

router = APIRouter(tags=["documents"])


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/documents/{document_id}/chunk", response_model=list[DocumentChunkRead], status_code=status.HTTP_201_CREATED)
def create_document_chunks(document_id: int, db: Session = Depends(get_db)) -> list[DocumentChunk]:
    document = db.query(Document).filter(Document.id == document_id).first()
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    existing_chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_index).all()
    if existing_chunks:
        return existing_chunks

    if not document.content or not document.content.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Document content is empty")

    chunks = chunk_text(document.content, chunk_size=1000, overlap=150)
    saved_chunks: list[DocumentChunk] = []
    for idx, piece in enumerate(chunks):
        chunk = DocumentChunk(document_id=document_id, chunk_index=idx, content=piece, embedding=None)
        db.add(chunk)
        saved_chunks.append(chunk)
    db.commit()
    for chunk in saved_chunks:
        db.refresh(chunk)
    return saved_chunks


@router.get("/documents/{document_id}/chunks", response_model=list[DocumentChunkRead])
def list_document_chunks(document_id: int, db: Session = Depends(get_db)) -> list[DocumentChunk]:
    document = db.query(Document).filter(Document.id == document_id).first()
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    return db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_index).all()
