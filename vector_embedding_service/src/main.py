import json
import os
import time

import sentry_sdk
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field
from starlette.requests import Request
from starlette.responses import StreamingResponse

from src import common

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

        # TODO: Review if this is tunnel business is really secure
        if common.is_from_tunnel(request) and (jwt_token is None or not await common.is_valid_jwt_token(jwt_token.replace("Bearer ", ""))):
            raise HTTPException(status_code=401, detail="Invalid token.")

@app.get("/ping", dependencies=[Depends(AuthenticateToken())])
async def models() -> None:
    pass


if __name__ == "__main__":
    import uvicorn

    # if common.is_test_environment():
    #     import pydevd_pycharm
    #
    #     pydevd_pycharm.settrace("host.docker.internal", port=5678, stdoutToServer=True, stderrToServer=True, suspend=False)

    uvicorn.run(app, host="0.0.0.0", port=8000)
