from typing import Dict, Any, List

import aiohttp
import pytest

from src.models import Embedding, EmbeddingGet, EmbeddingQuery

BASE_URL: str ="http://0.0.0.0:8001"


@pytest.mark.asyncio
async def test_get_embeddings() -> None:
    url: str = f"{BASE_URL}/embeddings"
    json: Dict[Any, Any] = EmbeddingGet(input="The capital of France is Paris.",model="text-embedding-3-small").model_dump()

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=json) as response:
            assert response.status == 200

@pytest.mark.asyncio
async def test_upsert_embeddings() -> None:
    url: str = f"{BASE_URL}/database"
    text: str = "The capital of France is Paris."
    embedding: Embedding = Embedding(
        source="Testing",
        content=text,
        index="TEST",
        embedding_model="text-embedding-3-small"
    )

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=embedding.model_dump()) as response:
            assert response.status == 200

@pytest.mark.asyncio
async def test_query_embeddings() -> None:
    url: str = f"{BASE_URL}/database"
    text: str = "What is the capital of France?"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, json=EmbeddingQuery(input=text, index="TEST").model_dump()) as response:
            return_data: Dict[str, Any] = await response.json()
            assert len(return_data) > 0
