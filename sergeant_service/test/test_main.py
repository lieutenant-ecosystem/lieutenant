from typing import List

import httpx
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport, Client

from src.main import app, Message, ChatCompletionRequest

client = TestClient(app)

mock_message_list: List[Message] = [
    Message(role="user", content="What is the capital of France? Answer in one word only.")
]

mock_chat_completion_request: ChatCompletionRequest = ChatCompletionRequest(
    model="GPT-4o Mini (Custom)",
    messages=mock_message_list,
    max_tokens=100,
    temperature=0.7,
    stream=False
)


@pytest.mark.asyncio
async def test_chat_completion() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/chat/completions", content=mock_chat_completion_request.model_dump_json())

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_all_models() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/models")

    assert len(response.json()["data"]) > 0
