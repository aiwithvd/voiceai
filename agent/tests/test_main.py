import pytest
from httpx import AsyncClient, ASGITransport
from config import Settings
from main import create_app

@pytest.fixture
def test_settings():
    return Settings(
        LIVEKIT_URL="ws://localhost:7880",
        LIVEKIT_API_KEY="test_key",
        LIVEKIT_API_SECRET="test_secret",
    )

@pytest.mark.asyncio
async def test_health_endpoint(test_settings):
    app = create_app(test_settings)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"

@pytest.mark.asyncio
async def test_token_endpoint_returns_jwt(test_settings):
    app = create_app(test_settings)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/token?room=test-room&identity=test-user")
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    assert len(data["token"]) > 0

@pytest.mark.asyncio
async def test_token_missing_room(test_settings):
    app = create_app(test_settings)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/token")
    assert resp.status_code == 422
