import asyncio
import hashlib
import logging
import os
import time
from enum import Enum
from logging import Logger
from urllib.parse import urlparse, ParseResult

import aiohttp
from aiohttp import ClientError
from starlette.requests import Request

logger: Logger = logging.getLogger(__name__)


class Constants(Enum):
    DATA_PATH = "../data/"
    OPEN_WEBUI_URL = os.getenv("OPEN_WEBUI_URL")
    VECTOR_EMBEDDING_SERVICE_URL = os.getenv("VECTOR_EMBEDDING_SERVICE_URL")


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


async def wait_for_connection(url: str, timeout: int = 60) -> None:
    parse_result: ParseResult = urlparse(url)
    host: str = parse_result.hostname
    port: int = parse_result.port

    start_time: float = time.time()
    while True:
        try:
            logger.debug(f"Attempting to connect to {host}:{port}...")
            reader, writer = await asyncio.open_connection(host, port)
            logger.debug(f"Successfully connected to {host}:{port}")
            writer.close()
            await writer.wait_closed()
            return
        except (ConnectionRefusedError, OSError) as e:
            logger.error(f"Error while connecting to{host}:{port}: {str(e)}")

        elapsed: float = time.time() - start_time
        if elapsed >= timeout:
            raise TimeoutError(f"Could not connect to {host}:{port} within {timeout} seconds.")

        await asyncio.sleep(1)
