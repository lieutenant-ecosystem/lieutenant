import os
import time
from typing import Dict, Any

import httpx
import sentry_sdk
from fastapi import FastAPI, Depends, Body
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field
from starlette.requests import Request

start_up_time: int = int(time.time())

if os.getenv("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        traces_sample_rate=1.0,
        _experiments={"continuous_profiling_auto_start": True, },
    )
app = FastAPI(title="Vector Embedding Service API")


class AuthenticateToken(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(AuthenticateToken, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> None:
        jwt_token: str = request.headers.get("Authorization")

        # # TODO: Review if this tunnel business is really secure
        # if common.is_from_tunnel(request) and (
        #         jwt_token is None or not await common.is_valid_jwt_token(jwt_token.replace("Bearer ", ""))):
        #     raise HTTPException(status_code=401, detail="Invalid token.")


class EmbeddingRequest(BaseModel):
    input: str = Field(...)
    model: str = Field(default="text-embedding-3-small")


class EmbeddingUsage(BaseModel):
    prompt_tokens: int = Field(...)
    total_tokens: int = Field(...)


class EmbeddingData(BaseModel):
    object: str = Field(default="list")
    index: int
    embedding: list[float]


class EmbeddingResponse(BaseModel):
    object: str = Field(default="list")
    data: list[EmbeddingData]
    model: str = Field(default="text-embedding-3-small")
    usage: EmbeddingUsage


@app.post("/embeddings", dependencies=[Depends(AuthenticateToken())])
async def get_embeddings(request_body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    url: str = os.getenv("VECTOR_EMBEDDING_BASE_URL") or "https://api.openai.com/v1/embeddings"
    api_key: str = os.getenv("VECTOR_EMBEDDING_API_KEY") or os.getenv("OPENAI_API_KEY")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            json={"input": request_body["input"], "model": request_body["model"]},
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
        )

    return response.json()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
