import json
import os
import time
import uuid
from typing import Optional, List, Dict, AsyncGenerator

import sentry_sdk
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field
from starlette.requests import Request
from starlette.responses import StreamingResponse

from src import common
from src.sergeant import LLM, Sergeant

start_up_time: int = int(time.time())

if os.getenv("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        traces_sample_rate=1.0,
        _experiments={"continuous_profiling_auto_start": True, },
    )
app = FastAPI(title="Lieutenant API")


class AuthenticateToken(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(AuthenticateToken, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> None:
        jwt_token: str = request.headers.get("Authorization")

        # TODO: Review if this is tunnel business is really secure
        if common.is_from_tunnel(request) and (jwt_token is None or not await common.is_valid_jwt_token(jwt_token.replace("Bearer ", ""))):
            raise HTTPException(status_code=401, detail="Invalid token.")


class Message(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: LLM
    messages: List[Message]
    max_tokens: Optional[int] = Field(default=4096, le=8192)
    temperature: Optional[float] = Field(default=0.2, ge=0, le=2)
    stream: Optional[bool] = False


async def stream_response(llm: BaseChatModel, messages: List[Dict], request: ChatCompletionRequest) -> AsyncGenerator[str, None]:
    async for chunk in llm.astream(messages):
        token = chunk.content
        if token:
            yield f"data: {json.dumps({
                'id': str(uuid.uuid4()),
                'object': 'chat.completion.chunk',
                'created': int(time.time()),
                'model': request.model.value,
                'choices': [{'delta': {'content': token}}],
            })}\n\n"
    yield "data: [DONE]\n\n"


@app.post("/chat/completions", dependencies=[Depends(AuthenticateToken())], response_model=None)
async def chat_completions(request: ChatCompletionRequest) -> StreamingResponse | Dict:
    messages: List[Dict[str, str]] = [{"role": m.role, "content": m.content} for m in request.messages]
    llm: LLM = next(filter(lambda l: l == request.model, list(LLM)))
    sergeant: Sergeant = Sergeant.get(llm)
    sergeant.model.temperature = request.temperature
    sergeant.model.max_tokens = request.max_tokens

    try:
        if request.stream:
            return StreamingResponse(stream_response(sergeant.model, messages, request), media_type="text/event-stream")

        response: BaseMessage = await sergeant.model.ainvoke(messages)
        return {
            "id": str(uuid.uuid4()),
            "object": "chat.completion",
            "created": int(time.time()),
            "model": request.model.value,
            "choices": [{"message": {"role": "assistant", "content": response.content}}],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/models")
async def models() -> Dict[str, List[Dict[str, str | int]] | str]:
    return {
        "object": "list",
        "data": [{"id": sergeant.llm.value, "object": "model", "created": start_up_time, "owned_by": "N/A"} for sergeant in Sergeant.get_all()]
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
