from typing import Any

import aiohttp
import pytest

from src.models import BaseIntelligenceQuery
from src.officer.http_blob import HTTPBlobIntelligence

BASE_URL: str ="http://0.0.0.0:8002"


@pytest.mark.asyncio
async def test_upsert_http_blob() -> None:
    url: str = f"{BASE_URL}/http_blob"

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=HTTPBlobIntelligence(source="https://raw.githubusercontent.com/lieutenant-ecosystem/lieutenant/refs/heads/main/sergeant_service/mypy.ini").model_dump()) as response: # type: ignore[arg-type]
            assert response.status == 200

@pytest.mark.asyncio
async def test_get_http_blob() -> None:
    url: str = f"{BASE_URL}/http_blob"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, json=BaseIntelligenceQuery(query="Are imports missing?").model_dump()) as response:
            data: Any = await response.json()
            print(data)
            assert len(data) > 1
