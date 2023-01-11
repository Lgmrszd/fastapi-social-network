from fastapi.testclient import TestClient

from src.fastapi_social_network.app import app

client = TestClient(app)


def test_read_main():
    response = client.get("/")
    assert response.status_code == 404
