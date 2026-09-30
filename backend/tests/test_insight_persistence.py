from uuid import uuid4

from fastapi.testclient import TestClient

from app.db.database import SessionLocal
from app.db.init_db import init_db
from app.main import app
from app.models.document import Document
from app.models.evidence import Evidence
from app.models.insight import Insight
from app.models.source import Source
from app.schemas.extraction import ExtractedInsight
from app.services.insight_persistence import save_extracted_insights


init_db()

client = TestClient(app)


def _create_test_records():
    """Create a unique client, source, and document for a test."""
    unique_id = uuid4().hex[:8]

    response = client.post(
        "/clients",
        json={
            "name": f"Persistence Test {unique_id}",
            "description": "Automated persistence test",
        },
    )
    assert response.status_code == 201
    client_id = response.json()["id"]

    with SessionLocal() as db:
        source = Source(
            client_id=client_id,
            url=f"https://example.com/{unique_id}",
            title="Persistence Test Source",
            source_type="test",
        )
        db.add(source)
        db.flush()

        document = Document(
            source_id=source.id,
            title="Persistence Test Document",
            content="Test document content.",
            url=f"https://example.com/{unique_id}/article",
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        return client_id, document.id


def test_save_extracted_insight_creates_evidence_and_insight():
    client_id, document_id = _create_test_records()

    extracted = [
        ExtractedInsight(
            category="TECHNOLOGY",
            subject="AWS",
            observation="The person explicitly mentions AWS.",
            confidence="high",
            evidence_text="I have been working with AWS for three years.",
        )
    ]

    with SessionLocal() as db:
        saved = save_extracted_insights(
            db,
            client_id=client_id,
            document_id=document_id,
            extracted_insights=extracted,
        )
        db.commit()

        assert len(saved) == 1

        insight = saved[0]
        db.refresh(insight)

        assert insight.id is not None
        assert insight.client_id == client_id
        assert insight.category == "TECHNOLOGY"
        assert insight.subject == "AWS"
        assert insight.evidence_id is not None

        evidence = db.query(Evidence).filter(
            Evidence.id == insight.evidence_id
        ).first()

        assert evidence is not None
        assert evidence.client_id == client_id
        assert evidence.document_id == document_id
        assert evidence.evidence_text == (
            "I have been working with AWS for three years."
        )
        assert evidence.confidence == "high"


def test_save_multiple_insights_creates_matching_evidence():
    client_id, document_id = _create_test_records()

    extracted = [
        ExtractedInsight(
            category="TECHNOLOGY",
            subject="AWS",
            observation="The person explicitly mentions AWS.",
            confidence="high",
            evidence_text="I have been working with AWS.",
        ),
        ExtractedInsight(
            category="HOBBY",
            subject="Golf",
            observation="The person explicitly states that they enjoy golf.",
            confidence="high",
            evidence_text="Outside work, I enjoy playing golf.",
        ),
    ]

    with SessionLocal() as db:
        saved = save_extracted_insights(
            db,
            client_id=client_id,
            document_id=document_id,
            extracted_insights=extracted,
        )
        db.commit()

        assert len(saved) == 2

        for insight in saved:
            db.refresh(insight)

            assert insight.evidence_id is not None

            evidence = db.query(Evidence).filter(
                Evidence.id == insight.evidence_id
            ).first()

            assert evidence is not None
            assert evidence.client_id == client_id
            assert evidence.document_id == document_id


def test_empty_extraction_creates_nothing():
    client_id, document_id = _create_test_records()

    with SessionLocal() as db:
        saved = save_extracted_insights(
            db,
            client_id=client_id,
            document_id=document_id,
            extracted_insights=[],
        )
        db.commit()

        assert saved == []

        evidence_count = db.query(Evidence).filter(
            Evidence.client_id == client_id,
            Evidence.document_id == document_id,
        ).count()

        insight_count = db.query(Insight).filter(
            Insight.client_id == client_id,
        ).count()

        assert evidence_count == 0
        assert insight_count == 0