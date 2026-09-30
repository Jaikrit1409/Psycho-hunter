from uuid import uuid4

from fastapi.testclient import TestClient

from app.db.database import SessionLocal
from app.db.init_db import init_db
from app.main import app
from app.models.document import Document
from app.models.evidence import Evidence
from app.models.insight import Insight
from app.models.source import Source

init_db()

client = TestClient(app)


def _create_test_document(content: str):
    unique_id = uuid4().hex[:8]

    response = client.post(
        "/clients",
        json={
            "name": f"Extraction API Test {unique_id}",
            "description": "Automated extraction API test",
        },
    )

    assert response.status_code == 201

    client_id = response.json()["id"]

    with SessionLocal() as db:
        source = Source(
            client_id=client_id,
            url=f"https://example.com/{unique_id}",
            title="Extraction Test Source",
            source_type="test",
        )

        db.add(source)
        db.flush()

        document = Document(
            source_id=source.id,
            title="Extraction Test Document",
            content=content,
            url=f"https://example.com/{unique_id}/article",
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        return client_id, document.id


def test_extract_document_creates_insights_and_evidence():
    client_id, document_id = _create_test_document(
        "I have been working with AWS for three years. "
        "Outside work, I enjoy playing golf."
    )

    response = client.post(
        f"/documents/{document_id}/extract"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["document_id"] == document_id
    assert data["client_id"] == client_id

    assert len(data["insights"]) == 2

    subjects = {
        insight["subject"]
        for insight in data["insights"]
    }

    assert "AWS" in subjects
    assert "Golf" in subjects

    with SessionLocal() as db:
        insights = (
            db.query(Insight)
            .filter(Insight.client_id == client_id)
            .all()
        )

        evidence = (
            db.query(Evidence)
            .filter(
                Evidence.client_id == client_id,
                Evidence.document_id == document_id,
            )
            .all()
        )

        assert len(insights) == 2
        assert len(evidence) == 2


def test_extract_document_does_not_create_duplicates():
    client_id, document_id = _create_test_document(
        "I work with Python and AWS. "
        "In my free time, I enjoy golf."
    )

    first_response = client.post(
        f"/documents/{document_id}/extract"
    )

    assert first_response.status_code == 200

    second_response = client.post(
        f"/documents/{document_id}/extract"
    )

    assert second_response.status_code == 200

    with SessionLocal() as db:
        insight_count = (
            db.query(Insight)
            .filter(Insight.client_id == client_id)
            .count()
        )

        evidence_count = (
            db.query(Evidence)
            .filter(
                Evidence.client_id == client_id,
                Evidence.document_id == document_id,
            )
            .count()
        )

        assert insight_count == 3
        assert evidence_count == 3


def test_extract_missing_document_returns_404():
    response = client.post(
        "/documents/999999999/extract"
    )

    assert response.status_code == 404


def test_extract_empty_document_returns_422():
    _, document_id = _create_test_document("")

    response = client.post(
        f"/documents/{document_id}/extract"
    )

    assert response.status_code == 422