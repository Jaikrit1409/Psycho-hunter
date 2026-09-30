from __future__ import annotations

from datetime import datetime
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from app.api.routes.sources import router as sources_router
from app.db.database import SessionLocal
from app.db.init_db import init_db
from app.main import app
from app.models.document import Document

init_db()

client = TestClient(app)


def test_create_source_for_existing_client() -> None:
    create_response = client.post("/clients", json={"name": "Source Client", "description": "Test client"})
    assert create_response.status_code == 201
    client_id = create_response.json()["id"]

    payload = {
        "url": "https://example.com/article",
        "source_type": "news",
        "title": "Example article",
        "publisher": "Example Media",
    }
    response = client.post(f"/clients/{client_id}/sources", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["client_id"] == client_id
    assert data["url"] == "https://example.com/article"
    assert data["source_type"] == "news"
    assert data["publisher"] == "Example Media"


def test_create_source_for_nonexistent_client() -> None:
    response = client.post(
        "/clients/999999/sources",
        json={"url": "https://example.com/missing", "source_type": "news"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Client not found"


def test_list_sources_for_client() -> None:
    create_response = client.post("/clients", json={"name": "Source List Client"})
    client_id = create_response.json()["id"]
    client.post(
        f"/clients/{client_id}/sources",
        json={"url": "https://example.com/list-one", "source_type": "blog"},
    )
    client.post(
        f"/clients/{client_id}/sources",
        json={"url": "https://example.com/list-two", "source_type": "blog"},
    )

    response = client.get(f"/clients/{client_id}/sources")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    assert {item["url"] for item in data}.issuperset({"https://example.com/list-one", "https://example.com/list-two"})


def test_list_sources_for_nonexistent_client() -> None:
    response = client.get("/clients/999999/sources")
    assert response.status_code == 404
    assert response.json()["detail"] == "Client not found"


def test_get_source() -> None:
    create_response = client.post("/clients", json={"name": "Source Fetch Client"})
    client_id = create_response.json()["id"]
    create_source_response = client.post(
        f"/clients/{client_id}/sources",
        json={"url": "https://example.com/fetch", "source_type": "press"},
    )
    source_id = create_source_response.json()["id"]

    response = client.get(f"/sources/{source_id}")
    assert response.status_code == 200
    assert response.json()["id"] == source_id


def test_get_nonexistent_source() -> None:
    response = client.get("/sources/999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Source not found"


def test_delete_source() -> None:
    create_response = client.post("/clients", json={"name": "Source Delete Client"})
    client_id = create_response.json()["id"]
    create_source_response = client.post(
        f"/clients/{client_id}/sources",
        json={"url": "https://example.com/delete", "source_type": "news"},
    )
    source_id = create_source_response.json()["id"]

    response = client.delete(f"/sources/{source_id}")
    assert response.status_code == 204

    get_response = client.get(f"/sources/{source_id}")
    assert get_response.status_code == 404


def test_source_url_validation() -> None:
    response = client.post(
        "/clients/1/sources",
        json={"url": "not-a-valid-url", "source_type": "news"},
    )
    assert response.status_code == 422


def test_source_route_paths_are_exact() -> None:
    source_paths = {route.path for route in sources_router.routes if hasattr(route, "path")}
    assert "/clients/{client_id}/sources" in source_paths
    assert "/sources/{source_id}" in source_paths
    assert "/clients/sources/{source_id}" not in source_paths


def test_ingest_source_success() -> None:
    create_client_response = client.post("/clients", json={"name": "Ingest Client", "description": "Has sources"})
    client_id = create_client_response.json()["id"]
    create_source_response = client.post(
        f"/clients/{client_id}/sources",
        json={"url": "https://example.com/ingest", "source_type": "news", "title": "Original Source"},
    )
    source_id = create_source_response.json()["id"]

    html = """
    <html>
      <head>
        <title>Example Article</title>
        <meta name="pubdate" content="2024-01-02T03:04:05Z" />
      </head>
      <body>
        <nav>Menu</nav>
        <main>
          <h1>Example Article</h1>
          <p>This is the first paragraph of useful content.</p>
          <p>This is the second paragraph of useful content.</p>
        </main>
      </body>
    </html>
    """
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "text/html; charset=utf-8"}
    mock_response.url = "https://example.com/ingest"
    mock_response.text = html
    mock_response.content = html.encode("utf-8")
    mock_response.raise_for_status.return_value = None

    with patch("app.api.routes.sources.requests.get", return_value=mock_response):
        response = client.post(f"/sources/{source_id}/ingest")

    assert response.status_code == 201
    data = response.json()
    assert data["source_id"] == source_id
    assert data["title"] == "Example Article"
    assert "first paragraph of useful content" in data["content"]
    assert data["published_at"] == "2024-01-02T03:04:05Z"
    assert data["collected_at"] is not None
    assert data["content_hash"]


def test_ingest_source_not_found() -> None:
    response = client.post("/sources/999999/ingest")
    assert response.status_code == 404
    assert response.json()["detail"] == "Source not found"


def test_ingest_source_invalid_url() -> None:
    create_client_response = client.post("/clients", json={"name": "Invalid Url Client"})
    client_id = create_client_response.json()["id"]
    source_response = client.post(
        f"/clients/{client_id}/sources",
        json={"url": "https://example.com/bad", "source_type": "news", "title": "Bad Source"},
    )
    source_id = source_response.json()["id"]

    with patch("app.api.routes.sources.requests.get", side_effect=Exception("connection failed")):
        response = client.post(f"/sources/{source_id}/ingest")

    assert response.status_code in {400, 502}


def test_document_created_and_source_association() -> None:
    create_client_response = client.post("/clients", json={"name": "Document Client"})
    client_id = create_client_response.json()["id"]
    source_response = client.post(
        f"/clients/{client_id}/sources",
        json={"url": "https://example.com/document-source", "source_type": "news", "title": "Source Title"},
    )
    source_id = source_response.json()["id"]

    html = """
    <html><head><title>Document Site</title></head><body><p>Document content is stored here.</p></body></html>
    """
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "text/html"}
    mock_response.url = "https://example.com/document-source"
    mock_response.text = html
    mock_response.content = html.encode("utf-8")
    mock_response.raise_for_status.return_value = None

    with patch("app.api.routes.sources.requests.get", return_value=mock_response):
        response = client.post(f"/sources/{source_id}/ingest")

    assert response.status_code == 201
    document_id = response.json()["id"]
    with SessionLocal() as db:
        stored_document = db.query(Document).filter(Document.id == document_id).first()
        assert stored_document is not None
        assert stored_document.source_id == source_id
        assert stored_document.title == "Document Site"
        assert "Document content is stored here" in stored_document.content
        assert stored_document.content_hash


def test_content_hash_is_stable_for_identical_content() -> None:
    create_client_response = client.post("/clients", json={"name": "Hash Client"})
    client_id = create_client_response.json()["id"]
    source_response = client.post(
        f"/clients/{client_id}/sources",
        json={"url": "https://example.com/hash", "source_type": "news", "title": "Hash Source"},
    )
    source_id = source_response.json()["id"]

    html = """
    <html><head><title>Repeated Title</title></head><body><p>The same article text appears again.</p></body></html>
    """
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "text/html"}
    mock_response.url = "https://example.com/hash"
    mock_response.text = html
    mock_response.content = html.encode("utf-8")
    mock_response.raise_for_status.return_value = None

    with patch("app.api.routes.sources.requests.get", return_value=mock_response):
        first_response = client.post(f"/sources/{source_id}/ingest")
        second_response = client.post(f"/sources/{source_id}/ingest")

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert first_response.json()["content_hash"] == second_response.json()["content_hash"]


def test_collected_at_and_content_hash_have_expected_shape() -> None:
    create_client_response = client.post("/clients", json={"name": "Shape Client"})
    client_id = create_client_response.json()["id"]
    source_response = client.post(
        f"/clients/{client_id}/sources",
        json={"url": "https://example.com/shape", "source_type": "news", "title": "Shape Source"},
    )
    source_id = source_response.json()["id"]

    html = """<html><body><h1>Shape Test</h1><p>Sample content for checksum validation.</p></body></html>"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "text/html"}
    mock_response.url = "https://example.com/shape"
    mock_response.text = html
    mock_response.content = html.encode("utf-8")
    mock_response.raise_for_status.return_value = None

    with patch("app.api.routes.sources.requests.get", return_value=mock_response):
        response = client.post(f"/sources/{source_id}/ingest")

    payload = response.json()
    assert payload["collected_at"] is not None
    datetime.fromisoformat(payload["collected_at"].replace("Z", "+00:00"))
    assert payload["content_hash"]
