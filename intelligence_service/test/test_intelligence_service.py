from typing import Any

import aiohttp
import pytest

from src.models import BaseIntelligenceQuery
from src.officer.http_blob import BaseIntelligence

BASE_URL: str = "http://0.0.0.0:8002"


@pytest.mark.asyncio
async def test_upsert_http_blob() -> None:
    url: str = f"{BASE_URL}/http_blob"

    async with aiohttp.ClientSession() as session:
        async with session.post(url,
                                json=BaseIntelligence(source="https://raw.githubusercontent.com/lieutenant-ecosystem/lieutenant/refs/heads/main/sergeant_service/mypy.ini", index="TEST").model_dump()) as response:  # type: ignore[arg-type]
            assert response.status == 200


@pytest.mark.asyncio
async def test_get_http_blob() -> None:
    url: str = f"{BASE_URL}/http_blob"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, json=BaseIntelligenceQuery(query="Are imports missing?", index="TEST").model_dump()) as response:
            data: Any = await response.json()
            print(data)
            assert len(data) > 1


@pytest.mark.asyncio
async def test_upsert_http_archive() -> None:
    url: str = f"{BASE_URL}/http_archive"

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=BaseIntelligence(source="https://codeload.github.com/lieutenant-ecosystem/lieutenant/zip/refs/heads/main", index="TEST").model_dump()) as response:  # type: ignore[arg-type]
            assert response.status == 200


@pytest.mark.asyncio
async def test_get_http_archive() -> None:
    url: str = f"{BASE_URL}/http_archive"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, json=BaseIntelligenceQuery(query="Which code adds content from indexes?", index="TEST").model_dump()) as response:
            data = await response.json()
            print(data)
            assert len(data) > 1
