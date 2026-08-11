from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import pytest


@pytest.fixture
def client():
    with patch("app.core.database.engine"), \
         patch("app.core.database.SessionLocal"), \
         patch("app.core.redis_client.get_redis", return_value=MagicMock()):
        from app.main import app
        return TestClient(app)


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "auth-service"
