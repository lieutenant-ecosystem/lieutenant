import logging
import os
import time
from typing import Dict, Any, List

import sentry_sdk
from fastapi import FastAPI, Depends, Body
from fastapi.security import HTTPBearer
from starlette.exceptions import HTTPException
from starlette.requests import Request

from src import common
from src.models import EmbeddingQuery, Embedding

if os.getenv("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        traces_sample_rate=1.0,
        _experiments={"continuous_profiling_auto_start": True, },
    )
app = FastAPI(title="Vector Embedding Service API")
logging.basicConfig(level=logging.DEBUG if common.is_test_environment() else logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


class AuthenticateToken(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(AuthenticateToken, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> None:
        jwt_token: str = request.headers.get("Authorization")

        # TODO: Review if this tunnel business is really secure
        if common.is_from_tunnel(request) and (
                jwt_token is None or not await common.is_valid_jwt_token(jwt_token.replace("Bearer ", ""))):
            raise HTTPException(status_code=401, detail="Invalid token.")


@app.post("/database", dependencies=[Depends(AuthenticateToken())])
async def upsert_embedding(embedding: Embedding) -> None:
    embedding.upsert()


@app.get("/database", dependencies=[Depends(AuthenticateToken())])
async def query(embedding_query: EmbeddingQuery) -> List[Embedding]:
    return Embedding.query(embedding_query.input, embedding_query.index)


@app.post("/embeddings", dependencies=[Depends(AuthenticateToken())])
async def get_embeddings(request_body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    return await Embedding.get_raw_embedding(request_body["input"], request_body["model"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="debug" if common.is_test_environment() else "info")
