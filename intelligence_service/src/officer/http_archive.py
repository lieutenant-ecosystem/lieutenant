import logging
import os
import tempfile
import zipfile
from logging import Logger
from typing import List, Dict, Any, Tuple

import aiohttp
import yaml
from pydantic import BaseModel

from src.models import BaseOfficer, BaseIntelligence, ScheduledTask

logger: Logger = logging.getLogger(__name__)


class HTTPArchiveConfig(BaseModel):
    name: str
    source: str
    index: str
    description: str
    update_schedule: str
    update_on_start_up: bool

    @staticmethod
    def get() -> List["HTTPArchiveConfig"]:
        with open("data/http-archive.yml", "r") as raw_string:
            raw_data_list: List[Dict[str, Any]] = yaml.safe_load(raw_string)

        if raw_data_list is None:
            return []

        return [HTTPArchiveConfig(**raw_data) for raw_data in raw_data_list]


class HTTPArchive(BaseOfficer):

    @staticmethod
    async def _get_file_bytes(url: str) -> bytes:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                return await response.read()

    @staticmethod
    async def _get_file_archive_content(url: str) -> List[Tuple[str, str]]:
        content: bytes = await HTTPArchive._get_file_bytes(url)

        with tempfile.TemporaryDirectory() as tmp_dir_name:
            archive_path = os.path.join(tmp_dir_name, "archive.zip")
            with open(archive_path, "wb") as f:
                f.write(content)

            extracted_files: List[Tuple[str, str]] = []
            with zipfile.ZipFile(archive_path, "r") as zip_ref:
                zip_ref.extractall(tmp_dir_name)
                os.remove(archive_path)

                for root, _, files in os.walk(tmp_dir_name):
                    for file in files:
                        file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(file_path, tmp_dir_name)
                        with open(file_path, "r", encoding="utf-8") as f_read:
                            file_content = f_read.read()

                        extracted_files.append((relative_path, file_content))

        return extracted_files

    @staticmethod
    def get_scheduled_tasks() -> List[ScheduledTask]:  # type: ignore[override]
        scheduled_task_list: List[ScheduledTask] = []
        for http_blob_config in HTTPArchiveConfig.get():
            intelligence: BaseIntelligence = BaseIntelligence(source=http_blob_config.source, description=http_blob_config.description, index=http_blob_config.index)  # type: ignore[arg-type]

            async def update() -> None:
                logger.info(f"Updating Index on Schedule: {http_blob_config.name} | {http_blob_config.index}")
                await HTTPArchive.upsert(intelligence)
                logger.info(f"Updating Index on Schedule completed: {http_blob_config.index}")

            scheduled_task_list.append(ScheduledTask(
                name=f"{http_blob_config.name} Updater",
                update_func=update,
                update_schedule=http_blob_config.update_schedule
            ))

        return scheduled_task_list

    @staticmethod
    async def update_on_startup() -> None:

        for http_blob_config in HTTPArchiveConfig.get():
            intelligence: BaseIntelligence = BaseIntelligence(source=http_blob_config.source, description=http_blob_config.description, index=http_blob_config.index)  # type: ignore[arg-type]
            if http_blob_config.update_on_start_up:
                logger.info(f"Updating Index on Startup: {http_blob_config.name} | {http_blob_config.index}")
                await HTTPArchive.upsert(intelligence)
                logger.info(f"Updating Index on Startup completed: {http_blob_config.index}")

    @staticmethod
    async def upsert(intelligence: BaseIntelligence) -> None:
        if not isinstance(intelligence, BaseIntelligence):
            raise ValueError("The data is not valid: " + intelligence.model_dump_json())

        content_list: List[Tuple[str, str]] = await HTTPArchive._get_file_archive_content(intelligence.source)
        for content in content_list:
            intelligence.source = content[0]
            intelligence.content = content[1]

            await intelligence.upsert()
