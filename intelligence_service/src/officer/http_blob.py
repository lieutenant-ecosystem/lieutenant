from typing import List, Any, Dict

import aiohttp
import yaml
from pydantic import BaseModel

from src.models import BaseOfficer, BaseIntelligence


class HTTPBlobConfig(BaseModel):
    name: str
    source: str
    description: str

    @staticmethod
    def get() -> List["HTTPBlobConfig"]:
        with open("data/http-blob.yml", "r") as raw_string:
            raw_data_list: List[Dict[str, Any]] = yaml.safe_load(raw_string)

        return [HTTPBlobConfig(**raw_data) for raw_data in raw_data_list]


class HTTPBlobIntelligence(BaseIntelligence):
    def __init__(self, **kwargs: Dict[str, Any]):
        super().__init__(**kwargs)


class HTTPBlob(BaseOfficer):

    @staticmethod
    async def update() -> None:
        for http_blob_config in HTTPBlobConfig.get():
            print(f"Updating intelligence for: {http_blob_config.name}")
            intelligence: HTTPBlobIntelligence = HTTPBlobIntelligence(source=http_blob_config.source, description=http_blob_config.description) # type: ignore[arg-type]
            await HTTPBlob.upsert(intelligence)
            print(f"Intelligence updated for: {http_blob_config.name}")

    @staticmethod
    async def _get_file_content(url: str) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                data: bytes = await response.read()

        return data.decode("utf-8")

    @staticmethod
    async def upsert(intelligence: BaseIntelligence) -> None:
        if not isinstance(intelligence, HTTPBlobIntelligence):
            raise ValueError("The data is not valid: " + intelligence.model_dump_json())

        content: str = await HTTPBlob._get_file_content(intelligence.source)
        intelligence.content = (f"# Source"
                                f"\n{intelligence.source}"
                                f"\n\n# Description"
                                f"\n{intelligence.description}"
                                f"\n\n# Content"
                                f"\n{content}")

        await intelligence.upsert()
