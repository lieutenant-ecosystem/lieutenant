import logging
from logging import Logger
from typing import List, Any, Dict

import aiohttp
import yaml
from common import Constants
from models import BaseOfficer, BaseIntelligence, ScheduledTask
from pydantic import BaseModel

logger: Logger = logging.getLogger(__name__)


class HTTPBlobConfig(BaseModel):
    name: str
    source: str
    index: str
    description: str
    update_schedule: str
    update_on_start_up: bool

    @staticmethod
    def get() -> List["HTTPBlobConfig"]:
        with open(f"{Constants.DATA_PATH.value}http-blob.yml", "r") as raw_string:
            raw_data_list: List[Dict[str, Any]] = yaml.safe_load(raw_string)

        if raw_data_list is None:
            return []

        return [HTTPBlobConfig(**raw_data) for raw_data in raw_data_list]


class HTTPBlob(BaseOfficer):

    @staticmethod
    async def _get_file_content(url: str) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                data: bytes = await response.read()

        return data.decode("utf-8")

    @staticmethod
    def get_scheduled_tasks() -> List[ScheduledTask]:
        scheduled_task_list: List[ScheduledTask] = []
        for http_blob_config in HTTPBlobConfig.get():
            intelligence: BaseIntelligence = BaseIntelligence(source=http_blob_config.source, description=http_blob_config.description, index=http_blob_config.index)

            async def update() -> None:
                logger.info(f"Updating Index on Schedule: {http_blob_config.name} | {http_blob_config.index}")
                logger.info(f"Updating Index on Schedule: {http_blob_config.name} | {http_blob_config.index}")
                await HTTPBlob.upsert(intelligence)
                logger.info(f"Updating Index on Schedule completed: {http_blob_config.name} | {http_blob_config.index}")

            scheduled_task_list.append(ScheduledTask(
                name=f"{http_blob_config.name} Updater",
                update_func=update,
                update_schedule=http_blob_config.update_schedule
            ))

        return scheduled_task_list

    @staticmethod
    async def update_on_startup() -> None:

        for http_blob_config in HTTPBlobConfig.get():
            intelligence: BaseIntelligence = BaseIntelligence(source=http_blob_config.source, description=http_blob_config.description, index=http_blob_config.index)
            if http_blob_config.update_on_start_up:
                logger.info(f"Updating Index on Startup: {http_blob_config.name} | {http_blob_config.index}")
                await HTTPBlob.upsert(intelligence)
                logger.info(f"Updating Index on Startup completed: {http_blob_config.name} | {http_blob_config.index}")

    @staticmethod
    async def upsert(intelligence: BaseIntelligence) -> None:
        if not isinstance(intelligence, BaseIntelligence):
            raise ValueError("The data is not valid: " + intelligence.model_dump_json())

        content: str = await HTTPBlob._get_file_content(intelligence.source)
        intelligence.content = (f"# Source"
                                f"\n{intelligence.source}"
                                f"\n\n# Description"
                                f"\n{intelligence.description}"
                                f"\n\n# Content"
                                f"\n{content}")

        await intelligence.upsert()
