import os
from enum import Enum

import aiohttp
from aiohttp import ClientError
from starlette.requests import Request


class Constants(Enum):
    DATA_PATH = f"../data/"
    LLM_YAML_PATH = f"{DATA_PATH}llm.yml"
    OPEN_WEBUI_URL = os.getenv("OPEN_WEBUI_URL")


def is_production_environment() -> bool:
    return os.environ.get('ENVIRONMENT') == 'production'


def is_test_environment() -> bool:
    return not is_production_environment()


def is_from_tunnel(request: Request) -> bool:
    return "X-Forwarded-For" in request.headers


async def is_valid_jwt_token(jwt_token: str) -> bool:
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{Constants.OPEN_WEBUI_URL.value}/api/models", headers={'Authorization': f'Bearer {jwt_token}'}) as response:
                return response.status == 200
        except ClientError:
            return False
