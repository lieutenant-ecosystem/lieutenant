from typing import List, Dict, Any
import aiohttp
import pytest
from src.main import Message, ChatCompletionRequest

BASE_URL: str = "http://0.0.0.0:8000"

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
    url: str = f"{BASE_URL}/chat/completions"
    json: Dict[Any, Any] = mock_chat_completion_request.model_dump()

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=json) as response:
            data = await response.json()
            print(data)
            assert response.status == 200


@pytest.mark.asyncio
async def test_all_models() -> None:
    url: str = f"{BASE_URL}/models"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            print(data)
            assert len(data["data"]) > 0