import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from src.main import app

client = TestClient(app)

@pytest.mark.asyncio
async def test_ping() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/ping")

    assert response.status_code == 200
