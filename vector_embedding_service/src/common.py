import hashlib
import os
from enum import Enum

import aiohttp
from aiohttp import ClientError
from starlette.requests import Request


class Constants(Enum):
    OPEN_WEBUI_PORT = "80"
    OPEN_WEBUI_URL = f"http://lieutenant-service:{OPEN_WEBUI_PORT}"


def is_production_environment() -> bool:
    return os.environ.get('ENVIRONMENT') == 'production'


def is_test_environment() -> bool:
    return not is_production_environment()


def is_from_tunnel(request: Request) -> bool:
    return "X-Forwarded-For" in request.headers


def get_sha256_hash(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


async def is_valid_jwt_token(jwt_token: str) -> bool:
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{Constants.OPEN_WEBUI_URL.value}/api/models", headers={'Authorization': f'Bearer {jwt_token}'}) as response:
                return response.status == 200
        except ClientError:
            return False
