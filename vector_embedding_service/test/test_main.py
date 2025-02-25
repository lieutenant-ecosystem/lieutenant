from typing import Dict, Any

import aiohttp
import pytest

from src.main import EmbeddingRequest

BASE_URL: str ="http://0.0.0.0:8001"


@pytest.mark.asyncio
async def test_get_embeddings() -> None:
    url: str = f"{BASE_URL}/embeddings"
    json: Dict[Any, Any] = EmbeddingRequest(input="What is the capital of France?",model="text-embedding-3-small").model_dump()

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=json) as response:
            assert response.status == 200
