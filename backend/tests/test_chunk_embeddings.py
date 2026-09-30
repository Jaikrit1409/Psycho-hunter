from unittest.mock import patch

import pytest
from app.db.database import SessionLocal
from app.db.init_db import init_db
from app.models.client import Client
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.source import Source
from app.services.chunk_embeddings import create_chunk_embedding


def test_create_chunk_embedding():
    init_db()

    db = SessionLocal()

    try:
        client = Client(
            name="Embedding Test Client",
        )
        db.add(client)
        db.flush()

        source = Source(
            client_id=client.id,
            url="https://example.com/embedding-test",
            source_type="website",
        )
        db.add(source)
        db.flush()

        document = Document(
            source_id=source.id,
            title="Embedding Test",
            content="Python and AWS are used in this project.",
        )
        db.add(document)
        db.flush()

        chunk = DocumentChunk(
            document_id=document.id,
            chunk_index=0,
            content="Python and AWS are used in this project.",
            embedding=None,
        )
        db.add(chunk)
        db.commit()
        db.refresh(chunk)

        fake_embedding = [0.1, 0.2, 0.3]

        with patch(
            "app.services.chunk_embeddings.create_embedding",
            return_value=fake_embedding,
        ):
            result = create_chunk_embedding(
                db,
                chunk_id=chunk.id,
            )

        assert result.id == chunk.id
        assert result.embedding == fake_embedding

    finally:
        db.close()


def test_create_chunk_embedding_missing_chunk():
    init_db()

    db = SessionLocal()

    try:
        with pytest.raises(
            ValueError,
            match="Document chunk not found",
        ):
            create_chunk_embedding(
                db,
                chunk_id=999999999,
            )

    finally:
        db.close()


def test_create_chunk_embedding_empty_content():
    init_db()

    db = SessionLocal()

    try:
        client = Client(
            name="Empty Chunk Client",
        )
        db.add(client)
        db.flush()

        source = Source(
            client_id=client.id,
            url="https://example.com/empty-test",
            source_type="website",
        )
        db.add(source)
        db.flush()

        document = Document(
            source_id=source.id,
            title="Empty Test",
            content="Some document",
        )
        db.add(document)
        db.flush()

        chunk = DocumentChunk(
            document_id=document.id,
            chunk_index=0,
            content="",
            embedding=None,
        )
        db.add(chunk)
        db.commit()
        db.refresh(chunk)

        with pytest.raises(
            ValueError,
            match="Document chunk content is empty",
        ):
            create_chunk_embedding(
                db,
                chunk_id=chunk.id,
            )

    finally:
        db.close()