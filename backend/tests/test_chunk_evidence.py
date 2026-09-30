from uuid import uuid4

from app.db.database import SessionLocal
from app.db.init_db import init_db
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.source import Source
from app.services.chunk_evidence import find_evidence_chunk

init_db()


def _create_test_document():
    unique_id = uuid4().hex[:8]

    with SessionLocal() as db:
        from app.models.client import Client

        client = Client(
            name=f"Chunk Evidence Test {unique_id}",
            description="Automated chunk evidence test",
        )

        db.add(client)
        db.flush()

        source = Source(
            client_id=client.id,
            url=f"https://example.com/{unique_id}",
            title="Chunk Evidence Source",
            source_type="test",
        )

        db.add(source)
        db.flush()

        document = Document(
            source_id=source.id,
            title="Chunk Evidence Document",
            content="Test document content.",
            url=f"https://example.com/{unique_id}/article",
        )

        db.add(document)
        db.flush()

        chunk_one = DocumentChunk(
            document_id=document.id,
            chunk_index=0,
            content="I have been working with AWS for three years.",
        )

        chunk_two = DocumentChunk(
            document_id=document.id,
            chunk_index=1,
            content="Outside work, I enjoy playing golf.",
        )

        db.add_all([chunk_one, chunk_two])
        db.commit()

        return document.id


def test_find_evidence_chunk():
    document_id = _create_test_document()

    with SessionLocal() as db:
        chunk = find_evidence_chunk(
            db,
            document_id=document_id,
            evidence_text="I have been working with AWS for three years.",
        )

        assert chunk is not None
        assert chunk.chunk_index == 0


def test_find_second_evidence_chunk():
    document_id = _create_test_document()

    with SessionLocal() as db:
        chunk = find_evidence_chunk(
            db,
            document_id=document_id,
            evidence_text="Outside work, I enjoy playing golf.",
        )

        assert chunk is not None
        assert chunk.chunk_index == 1


def test_evidence_chunk_not_found():
    document_id = _create_test_document()

    with SessionLocal() as db:
        chunk = find_evidence_chunk(
            db,
            document_id=document_id,
            evidence_text="I enjoy playing tennis.",
        )

        assert chunk is None