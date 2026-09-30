from fastapi.testclient import TestClient

from app.db.database import SessionLocal
from app.db.init_db import init_db
from app.main import app
from app.models.document import Document
from app.models.evidence import Evidence
from app.models.source import Source

init_db()

client = TestClient(app)


def _create_client(name: str = "Insight Client") -> int:
    response = client.post("/clients", json={"name": name, "description": "Insight test client"})
    assert response.status_code == 201
    return response.json()["id"]


def _create_source(client_id: int, url: str = "https://example.com/source") -> int:
    response = client.post(
        f"/clients/{client_id}/sources",
        json={
            "url": url,
            "source_type": "news",
            "title": "Example Source",
            "publisher": "Example Media",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_document(source_id: int, title: str = "Example Document") -> int:
    with SessionLocal() as db:
        document = Document(
            source_id=source_id,
            title=title,
            content="A public article describing relevant activities and interests.",
            url="https://example.com/article",
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        return document.id


def _create_evidence(client_id: int, document_id: int, claim: str = "Publicly mentions golf") -> int:
    with SessionLocal() as db:
        evidence = Evidence(
            client_id=client_id,
            document_id=document_id,
            claim=claim,
            evidence_text="The article mentions golf practice and course attendance.",
            confidence="high",
        )
        db.add(evidence)
        db.commit()
        db.refresh(evidence)
        return evidence.id


def test_create_hobby_insight() -> None:
    client_id = _create_client("Hobby Client")
    response = client.post(
        f"/clients/{client_id}/insights",
        json={
            "category": "HOBBY",
            "subject": "Golf",
            "observation": "Public sources contain repeated references to golf.",
            "confidence": "high",
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["client_id"] == client_id
    assert payload["category"] == "HOBBY"
    assert payload["subject"] == "Golf"
    assert payload["confidence"] == "high"
    assert payload["evidence_id"] is None


def test_create_interest_insight() -> None:
    client_id = _create_client("Interest Client")
    response = client.post(
        f"/clients/{client_id}/insights",
        json={
            "category": "INTEREST",
            "subject": "Artificial intelligence",
            "observation": "Public materials repeatedly reference AI and machine learning work.",
            "confidence": "medium",
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["category"] == "INTEREST"
    assert payload["subject"] == "Artificial intelligence"
    assert payload["confidence"] == "medium"


def test_create_insight_for_nonexistent_client() -> None:
    response = client.post(
        "/clients/999999/insights",
        json={
            "category": "TOPIC",
            "subject": "Space exploration",
            "observation": "No source evidence available.",
            "confidence": "low",
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Client not found"


def test_get_client_insights() -> None:
    client_id = _create_client("List Insights Client")
    client.post(
        f"/clients/{client_id}/insights",
        json={
            "category": "HOBBY",
            "subject": "Photography",
            "observation": "Repeated public mentions of photography.",
            "confidence": "high",
        },
    )
    client.post(
        f"/clients/{client_id}/insights",
        json={
            "category": "TECHNOLOGY",
            "subject": "Electric vehicles",
            "observation": "Recurring public references to EVs.",
            "confidence": "medium",
        },
    )

    response = client.get(f"/clients/{client_id}/insights")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    assert {item["subject"] for item in data}.issuperset({"Photography", "Electric vehicles"})


def test_get_insights_for_nonexistent_client() -> None:
    response = client.get("/clients/999999/insights")
    assert response.status_code == 404
    assert response.json()["detail"] == "Client not found"


def test_get_individual_insight() -> None:
    client_id = _create_client("Single Insight Client")
    create_response = client.post(
        f"/clients/{client_id}/insights",
        json={
            "category": "PROJECT",
            "subject": "Programming",
            "observation": "Public materials mention programming and software work.",
            "confidence": "high",
        },
    )
    insight_id = create_response.json()["id"]

    response = client.get(f"/insights/{insight_id}")
    assert response.status_code == 200
    assert response.json()["id"] == insight_id
    assert response.json()["subject"] == "Programming"


def test_get_nonexistent_insight() -> None:
    response = client.get("/insights/999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Insight not found"


def test_invalid_confidence() -> None:
    client_id = _create_client("Bad Confidence Client")
    response = client.post(
        f"/clients/{client_id}/insights",
        json={
            "category": "HOBBY",
            "subject": "Cricket",
            "observation": "Public mentions of cricket are visible.",
            "confidence": "very_high",
        },
    )
    assert response.status_code == 422


def test_invalid_category() -> None:
    client_id = _create_client("Bad Category Client")
    response = client.post(
        f"/clients/{client_id}/insights",
        json={
            "category": "PSYCHOLOGY",
            "subject": "Affective traits",
            "observation": "This should be rejected.",
            "confidence": "low",
        },
    )
    assert response.status_code == 422


def test_valid_evidence_association() -> None:
    client_id = _create_client("Evidence Client")
    source_id = _create_source(client_id, "https://example.com/evidence-source")
    document_id = _create_document(source_id)
    evidence_id = _create_evidence(client_id, document_id, "Public source references golf practice")

    response = client.post(
        f"/clients/{client_id}/insights",
        json={
            "category": "HOBBY",
            "subject": "Golf",
            "observation": "Evidence traces to a public article discussing golf practice.",
            "confidence": "high",
            "evidence_id": evidence_id,
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["evidence_id"] == evidence_id
    assert payload["client_id"] == client_id


def test_nonexistent_evidence() -> None:
    client_id = _create_client("Missing Evidence Client")
    response = client.post(
        f"/clients/{client_id}/insights",
        json={
            "category": "TOPIC",
            "subject": "Programming",
            "observation": "Evidence is missing.",
            "confidence": "medium",
            "evidence_id": 999999,
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Evidence not found"


def test_evidence_belongs_to_another_client() -> None:
    owner_client_id = _create_client("Owner Client")
    other_client_id = _create_client("Other Client")
    source_id = _create_source(owner_client_id, "https://example.com/owner-source")
    document_id = _create_document(source_id)
    evidence_id = _create_evidence(owner_client_id, document_id, "Owner evidence")

    response = client.post(
        f"/clients/{other_client_id}/insights",
        json={
            "category": "INTEREST",
            "subject": "Photography",
            "observation": "Attempting to use another client's evidence.",
            "confidence": "low",
            "evidence_id": evidence_id,
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Evidence does not belong to this client"
