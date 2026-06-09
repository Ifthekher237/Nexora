from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_root_endpoint() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["app"] == "Nexora"
    assert response.json()["status"] == "running"


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["app"] == "Nexora"
    assert body["status"] == "healthy"


def test_system_health_endpoint() -> None:
    response = client.get("/health/system")

    assert response.status_code == 200
    body = response.json()
    assert body["app"] == "Nexora"
    assert body["backend_status"] == "running"
    assert body["local_first"] is True
