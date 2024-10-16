import asyncio
import json
import logging
import time
import uuid
from typing import Optional, List, Dict, AsyncGenerator
from venv import logger

from fastapi import FastAPI, HTTPException
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from starlette.responses import StreamingResponse

app = FastAPI(title="LangChain-OpenAI Chat API")


class Message(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    max_tokens: Optional[int] = Field(default=4096, le=8192)
    temperature: Optional[float] = Field(default=0.2, ge=0, le=2)
    stream: Optional[bool] = False


async def stream_response(llm: ChatOpenAI, messages: List[Dict], request: ChatCompletionRequest) -> AsyncGenerator[str, None]:
    async for chunk in llm.astream(messages):
        token = chunk.content
        if token:
            yield f"data: {json.dumps({
                'id': str(uuid.uuid4()),
                'object': 'chat.completion.chunk',
                'created': int(time.time()),
                'model': request.model,
                'choices': [{'delta': {'content': token}}],
            })}\n\n"
    yield "data: [DONE]\n\n"


@app.post("/chat/completions", response_model=None)
async def chat_completions(request: ChatCompletionRequest) -> StreamingResponse | Dict:
    llm = ChatOpenAI(
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        model_name="gpt-4o-mini"
    )

    messages = [{"role": m.role, "content": m.content} for m in request.messages]

    try:
        if request.stream:
            return StreamingResponse(stream_response(llm, messages, request), media_type="text/event-stream")

        response = await llm.ainvoke(messages)
        return {
            "id": str(uuid.uuid4()),
            "object": "chat.completion",
            "created": int(time.time()),
            "model": request.model,
            "choices": [{"message": {"role": "assistant", "content": response.content}}],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/models")
async def models() -> Dict[str, List[Dict[str, str | int]] | str]:
    return {
        "object": "list",
        "data": [
            {
                "id": "GPT-4o Mini",
                "object": "model",
                "created": 1686935002,
                "owned_by": "kavindu"
            }
        ]
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
