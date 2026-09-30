from __future__ import annotations

from fastapi.testclient import TestClient

from app.db.database import SessionLocal
from app.db.init_db import init_db
from app.main import app
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.chunking import chunk_text

init_db()

client = TestClient(app)


def _create_document(content: str, title: str = "Chunked Document") -> int:
    create_client_response = client.post("/clients", json={"name": "Chunk Client", "description": "Test chunking"})
    client_id = create_client_response.json()["id"]
    create_source_response = client.post(
        f"/clients/{client_id}/sources",
        json={
            "url": "https://example.com/chunked-source",
            "source_type": "news",
            "title": "Chunk Source",
            "publisher": "Example Media",
        },
    )
    source_id = create_source_response.json()["id"]

    with SessionLocal() as db:
        document = Document(
            source_id=source_id,
            title=title,
            content=content,
            url="https://example.com/chunked-article",
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        return document.id


def test_chunk_text_basic() -> None:
    text = "A B C D E F G H I J"
    chunks = chunk_text(text, chunk_size=5, overlap=2)
    assert chunks == ["A B C D E", "D E F G H", "G H I J"]


def test_chunk_text_short_document() -> None:
    chunks = chunk_text("A B C", chunk_size=10, overlap=2)
    assert chunks == ["A B C"]


def test_chunk_text_long_document() -> None:
    text = " ".join(str(i) for i in range(1, 31))
    chunks = chunk_text(text, chunk_size=10, overlap=3)
    assert len(chunks) > 1
    assert chunks[0].split()[:5] == ["1", "2", "3", "4", "5"]
    assert chunks[1].split()[:3] == ["8", "9", "10"]


def test_chunk_text_order_and_overlap() -> None:
    chunks = chunk_text("A B C D E F G H", chunk_size=4, overlap=2)
    assert chunks == ["A B C D", "C D E F", "E F G H"]


def test_chunk_text_invalid_values() -> None:
    try:
        chunk_text("A B C", chunk_size=0, overlap=0)
    except ValueError:
        pass
    else:
        raise AssertionError("chunk_size=0 should raise ValueError")

    try:
        chunk_text("A B C", chunk_size=5, overlap=5)
    except ValueError:
        pass
    else:
        raise AssertionError("overlap >= chunk_size should raise ValueError")


def test_chunk_text_empty_document() -> None:
    assert chunk_text("   \n\t  ") == []


def test_create_document_chunks() -> None:
    document_id = _create_document("alpha beta gamma delta epsilon zeta eta theta iota kappa")
    response = client.post(f"/documents/{document_id}/chunk")
    assert response.status_code == 201
    payload = response.json()
    assert isinstance(payload, list)
    assert len(payload) >= 1
    assert payload[0]["document_id"] == document_id
    assert "embedding" not in payload[0]


def test_get_document_chunks() -> None:
    document_id = _create_document("one two three four five six seven eight nine ten")
    client.post(f"/documents/{document_id}/chunk")
    response = client.get(f"/documents/{document_id}/chunks")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["chunk_index"] == 0
    assert [item["chunk_index"] for item in data] == sorted(item["chunk_index"] for item in data)


def test_repeated_chunk_endpoint_does_not_duplicate() -> None:
    document_id = _create_document("one two three four five six seven eight nine ten eleven twelve")
    first = client.post(f"/documents/{document_id}/chunk")
    second = client.post(f"/documents/{document_id}/chunk")
    assert first.status_code == 201
    assert second.status_code == 201
    assert len(first.json()) == len(second.json())
    first_ids = {item["id"] for item in first.json()}
    second_ids = {item["id"] for item in second.json()}
    assert first_ids == second_ids


def test_chunk_endpoint_for_nonexistent_document() -> None:
    response = client.post("/documents/999999/chunk")
    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found"


def test_get_chunks_for_nonexistent_document() -> None:
    response = client.get("/documents/999999/chunks")
    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found"


def test_embedding_remains_null() -> None:
    document_id = _create_document("This is a test document with several words for chunking.")
    client.post(f"/documents/{document_id}/chunk")
    with SessionLocal() as db:
        chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).all()
    assert chunks
    assert all(chunk.embedding is None for chunk in chunks)
