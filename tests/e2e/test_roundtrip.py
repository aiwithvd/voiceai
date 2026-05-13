import pytest
import requests

SERVER_URL = "http://localhost:8001"


@pytest.fixture(scope="module")
def ensure_agent_running():
    try:
        resp = requests.get(f"{SERVER_URL}/health", timeout=3)
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
    except (requests.ConnectionError, AssertionError):
        pytest.skip("Agent server not running on port 8001")


def test_health_endpoint(ensure_agent_running):
    resp = requests.get(f"{SERVER_URL}/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_token_generation(ensure_agent_running):
    resp = requests.get(f"{SERVER_URL}/token?room=test-room&identity=e2e-user")
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    assert isinstance(data["token"], str)
    assert len(data["token"]) > 50
