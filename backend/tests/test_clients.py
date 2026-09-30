from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_client() -> None:
    payload = {"name": "Acme Corp", "description": "Public company"}
    response = client.post("/clients", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Acme Corp"
    assert data["description"] == "Public company"
    assert "id" in data


def test_list_clients() -> None:
    response = client.get("/clients")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(item["name"] == "Acme Corp" for item in data)


def test_get_client() -> None:
    response = client.get("/clients")
    assert response.status_code == 200
    clients = response.json()
    assert clients
    client_id = clients[0]["id"]

    detail_response = client.get(f"/clients/{client_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == client_id


def test_get_nonexistent_client_returns_404() -> None:
    response = client.get("/clients/999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Client not found"
