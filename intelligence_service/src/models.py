from abc import ABC, abstractmethod
from typing import Optional, Any, Dict, List

import aiohttp
from pydantic import BaseModel

from src import common
from src.common import Constants


class BaseIntelligenceQuery(BaseModel):
    query: str


class BaseIntelligence(BaseModel, ABC):
    id: Optional[str] = None
    index: str
    source: str
    content: Optional[str] = None
    description: Optional[str] = None

    def __init__(self, **kwargs: Dict[str, Any]):
        super().__init__(**kwargs)
        if self.id is None and self.content is not None and self.content != "":
            self.id = common.get_sha256_hash(self.content)

    async def upsert(self) -> None:
        if self.id is None:
            self.id = common.get_sha256_hash(self.content)

        async with aiohttp.ClientSession() as session:
            async with session.post(f"{Constants.VECTOR_EMBEDDING_SERVICE_URL.value}/database", json={"source": self.source, "content": self.content, "index": self.index}) as response:
                response.raise_for_status()


class BaseOfficer(BaseModel, ABC):
    @staticmethod
    @abstractmethod
    async def update() -> None:
        pass

    @staticmethod
    @abstractmethod
    async def upsert(intelligence: BaseIntelligence) -> None:
        pass

    @classmethod
    async def get(cls, query: str) -> List[BaseIntelligence]:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{Constants.VECTOR_EMBEDDING_SERVICE_URL.value}/database", json={"input": query, "index": cls.__name__}) as response:
                response.raise_for_status()
                data_list: List[Dict[str, Any]] = await response.json()

        return [
            BaseIntelligence(
                id=data.get("id"),
                source=data.get("source"),
                content=data.get("content")
            ) for data in data_list
        ]
