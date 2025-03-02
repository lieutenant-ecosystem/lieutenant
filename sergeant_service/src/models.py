import time
import uuid
from typing import List, Optional, Dict, Any

from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field


class Message(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    max_tokens: Optional[int] = Field(default=None, le=8192)
    temperature: Optional[float] = Field(default=None, ge=0, le=2)
    stream: Optional[bool] = False


class ChatCompletionResponse(BaseModel):
    id: str = Field(default_factory=lambda a: str(uuid.uuid4()))
    object: str = "chat.completion"
    created: int = Field(default_factory=lambda a: time.time())
    model: str
    choices: List[Dict[str, Any]]

    @staticmethod
    def get(response: BaseMessage) -> "ChatCompletionResponse":
        return ChatCompletionResponse(
            model=response.response_metadata.get("model_name"),
            choices=[{"message": {"role": "assistant", "content": response.content}}]
        )
