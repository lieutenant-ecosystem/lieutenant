import asyncio
import hashlib
import os
import time
from enum import Enum

import aiohttp
from aiohttp import ClientError
from starlette.requests import Request


class Constants(Enum):
    OPEN_WEBUI_PORT = "80"
    OPEN_WEBUI_URL = f"http://lieutenant-service:{OPEN_WEBUI_PORT}"
    VECTOR_EMBEDDING_SERVICE_PORT = "82" #    82/8001
    VECTOR_EMBEDDING_SERVICE_URL = f"http://lieutenant-service:{VECTOR_EMBEDDING_SERVICE_PORT}"


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


async def wait_for_connection(host: str, port: int, timeout: int = 60) -> None:
    start_time: float = time.time()
    while True:
        try:
            print(f"Attempting to connect to {host}:{port}...")
            reader, writer = await asyncio.open_connection(host, port)
            print(f"Successfully connected to {host}:{port}")
            writer.close()
            await writer.wait_closed()
            return
        except (ConnectionRefusedError, OSError) as e:
            print(f"Error while connecting to{host}:{port}: {str(e)}")

        elapsed: float = time.time() - start_time
        if elapsed >= timeout:
            raise TimeoutError(f"Could not connect to {host}:{port} within {timeout} seconds.")

        await asyncio.sleep(1)
