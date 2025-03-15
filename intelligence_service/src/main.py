import logging
import os
from contextlib import asynccontextmanager
from logging import Logger
from typing import List, AsyncGenerator

import sentry_sdk
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from cron_descriptor import get_description
from fastapi import FastAPI, Depends
from fastapi.security import HTTPBearer
from starlette.exceptions import HTTPException
from starlette.requests import Request

import common
from common import Constants
from models import BaseOfficer
from officer.http_archive import HTTPArchive
from officer.http_blob import BaseIntelligence, HTTPBlob

if os.getenv("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        traces_sample_rate=1.0,
        _experiments={"continuous_profiling_auto_start": True, },
    )

scheduler = AsyncIOScheduler()
logging.basicConfig(level=logging.DEBUG if common.is_test_environment() else logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger: Logger = logging.getLogger(__name__)


@asynccontextmanager
async def update_intelligence(app: FastAPI) -> AsyncGenerator:
    await common.wait_for_connection(Constants.VECTOR_EMBEDDING_SERVICE_URL.value)

    for scheduled_task in HTTPBlob.get_scheduled_tasks() + HTTPArchive.get_scheduled_tasks():
        scheduler.add_job(
            scheduled_task.update_func,
            trigger=CronTrigger.from_crontab(scheduled_task.update_schedule),
            id=scheduled_task.name,
            name=scheduled_task.name,
            replace_existing=True
        )
        logger.debug(f"Added a task into the scheduler | {scheduled_task.name} | {scheduled_task.update_schedule} | {get_description(scheduled_task.update_schedule)}")
    scheduler.start()

    await HTTPBlob.update_on_startup()
    await HTTPArchive.update_on_startup()
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


@app.get("/", dependencies=[Depends(AuthenticateToken())])
async def get(query: str, index: str) -> List[BaseIntelligence]:
    return await BaseOfficer.get(query, index)


@app.post("/http_blob", dependencies=[Depends(AuthenticateToken())])
async def upsert_http_blob(intelligence: BaseIntelligence) -> None:
    await HTTPBlob.upsert(intelligence)


@app.post("/http_archive", dependencies=[Depends(AuthenticateToken())])
async def upsert_http_archive(intelligence: BaseIntelligence) -> None:
    await HTTPArchive.upsert(intelligence)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="debug" if common.is_test_environment() else "info")
