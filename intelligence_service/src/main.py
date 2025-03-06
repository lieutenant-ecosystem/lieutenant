import os
from contextlib import asynccontextmanager
from typing import List, AsyncGenerator

import sentry_sdk
from fastapi import FastAPI, Depends
from fastapi.security import HTTPBearer
from starlette.exceptions import HTTPException
from starlette.requests import Request

from src import common
from src.common import Constants
from src.models import BaseIntelligenceQuery
from src.officer.http_archive import HTTPArchive
from src.officer.http_blob import BaseIntelligence, HTTPBlob

if os.getenv("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        traces_sample_rate=1.0,
        _experiments={"continuous_profiling_auto_start": True, },
    )


@asynccontextmanager
async def update_intelligence(app: FastAPI) -> AsyncGenerator:
    await common.wait_for_connection(Constants.VECTOR_EMBEDDING_SERVICE_HOST.value, int(Constants.VECTOR_EMBEDDING_SERVICE_PORT.value))
    await HTTPBlob.update()
    await HTTPArchive.update()
    yield


app = FastAPI(title="Vector Embedding Service API", lifespan=update_intelligence)


class AuthenticateToken(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(AuthenticateToken, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> None:
        jwt_token: str = request.headers.get("Authorization")

        # TODO: Review if this tunnel business is really secure
        if common.is_from_tunnel(request) and (
                jwt_token is None or not await common.is_valid_jwt_token(jwt_token.replace("Bearer ", ""))):
            raise HTTPException(status_code=401, detail="Invalid token.")


@app.post("/http_blob", dependencies=[Depends(AuthenticateToken())])
async def upsert_http_blob(intelligence: BaseIntelligence) -> None:
    await HTTPBlob.upsert(intelligence)


@app.get("/http_blob", dependencies=[Depends(AuthenticateToken())])
async def get_http_blob(intelligence_query: BaseIntelligenceQuery) -> List[BaseIntelligence]:
    return await HTTPBlob.get(intelligence_query.query, intelligence_query.index)


@app.post("/http_archive", dependencies=[Depends(AuthenticateToken())])
async def upsert_http_archive(intelligence: BaseIntelligence) -> None:
    await HTTPArchive.upsert(intelligence)


@app.get("/http_archive", dependencies=[Depends(AuthenticateToken())])
async def get_http_archive(intelligence_query: BaseIntelligenceQuery) -> List[BaseIntelligence]:
    return await HTTPArchive.get(intelligence_query.query, intelligence_query.index)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
