import logging
import os
from logging import Logger
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

import yaml
from common import Constants
from models import BaseOfficer, BaseIntelligence, ScheduledTask
from pydantic import BaseModel

from utility.jira_utility import Issue

logger: Logger = logging.getLogger(__name__)


class JiraConfig(BaseModel):
    name: str
    base_url: str
    index: str
    jql: str
    description: str
    update_schedule: str
    update_on_start_up: bool
    api_key: str

    @staticmethod
    def get() -> List["JiraConfig"]:
        with open(f"{Constants.DATA_PATH.value}jira.yml", "r") as raw_string:
            raw_data_list: List[Dict[str, Any]] = yaml.safe_load(raw_string) or []

        for raw_data in raw_data_list:
            raw_data["api_key"] = raw_data.get("api_key") or os.getenv(raw_data.get("api_key_environment_variable_key"))

        return [JiraConfig(**raw_data) for raw_data in raw_data_list]


class Jira(BaseOfficer):
    @staticmethod
    async def _get_ticket_content(source_url: str) -> Issue:
        source_config: Optional[JiraConfig] = next(filter(lambda c: urlparse(c.base_url).hostname == urlparse(source_url).hostname, JiraConfig.get()), None)
        if source_config is None:
            raise ValueError(f"No Jira Configuration found for the source: {source_url}")

        issue_id: str = urlparse(source_url).path.split("/")[-1]
        return await Issue.get_from_issue_id(issue_id, source_config.base_url, source_config.api_key)

    @staticmethod
    async def _get_all_ticket_content(base_url: str, jql: str) -> List[Issue]:
        source_config: Optional[JiraConfig] = next(filter(lambda c: c.base_url == base_url, JiraConfig.get()), None)
        if source_config is None:
            raise ValueError(f"No Jira Configuration found for this base URL: {base_url}")

        return await Issue.get_from_jql(jql, base_url, source_config.api_key)

    @staticmethod
    def get_scheduled_tasks() -> List[ScheduledTask]:
        #   TODO
        return []

    @staticmethod
    async def update_on_startup() -> None:
        #   TODO
        pass

    @staticmethod
    async def upsert(intelligence: BaseIntelligence) -> None:
        if not isinstance(intelligence, BaseIntelligence):
            raise ValueError("The data is not valid: " + intelligence.model_dump_json())

        intelligence.content = str(await Jira._get_ticket_content(intelligence.source) if intelligence.content is None else intelligence.content)
        await intelligence.upsert()
