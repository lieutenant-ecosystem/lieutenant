import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from src.main import app
from vector_embedding_service.src.main import EmbeddingRequest

client = TestClient(app)


@pytest.mark.asyncio
async def test_get_embeddings() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/embeddings", content=EmbeddingRequest(input="What is the capital of France?",
                                                                         model="text-embedding-3-small").model_dump_json())

    print(response.json())
    assert response.status_code == 200
