import os
import time
import uuid
from typing import List, Dict

import sentry_sdk
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer
from langchain_core.messages import BaseMessage
from starlette.requests import Request
from starlette.responses import StreamingResponse

from src import common
from src.sergeant import Sergeant, stream_response
from src.models import ChatCompletionRequest, ChatCompletionResponse

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


@app.post("/chat/completions", dependencies=[Depends(AuthenticateToken())], response_model=None)
async def chat_completions(request: ChatCompletionRequest) -> StreamingResponse | ChatCompletionResponse:
    sergeant: Sergeant = Sergeant.get(request.model)
    sergeant.model.temperature = request.temperature
    sergeant.model.max_tokens = request.max_tokens
    messages: List[Dict[str, str]] = Sergeant.get_messages(request, sergeant)

    try:
        if len(sergeant.indexes) > 0:
            sergeant.add_context_from_indexes(messages)

        if request.stream:
            return sergeant.ask_stream(messages, request)
        else:
            return await sergeant.ask(messages)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/models")
async def models() -> Dict[str, List[Dict[str, str | int]] | str]:
    return {
        "object": "list",
        "data": [{"id": sergeant.name, "object": "model", "created": start_up_time, "owned_by": "N/A"} for sergeant in Sergeant.get_all()]
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
