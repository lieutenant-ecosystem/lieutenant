import os
import uuid
from typing import Optional, List, Any, Dict

import httpx
from pydantic import BaseModel, Field
from sqlalchemy import select, func, literal

from src import database
from src.database import Vectors


class Embedding(BaseModel):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    source: str
    content: str
    index: str
    embeddings: List[float]

    async def upsert(self) -> None:
        if len(self.embeddings) != 1536:
            raise ValueError(f"Embeddings must be of dimension 1536, got {len(self.embeddings)}")

        vector = Vectors(
            content=self.content,
            source=self.source,
            index=self.index,
            embedding=self.embeddings
        )

        async for session in database.get_async_session():
            session.add(vector)
            await session.commit()
            break

    @staticmethod
    async def get_raw_embedding(content: str, model: str = "text-embedding-3-small") -> Dict[str, Any]:
        url: str = os.getenv("VECTOR_EMBEDDING_BASE_URL") or "https://api.openai.com/v1/embeddings"
        api_key: str = os.getenv("VECTOR_EMBEDDING_API_KEY") or os.getenv("OPENAI_API_KEY")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json={"input": content, "model": model},
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
            )

            response.raise_for_status()  # Ensure the request was successful
            return response.json()

    @staticmethod
    async def get_embedding(content: str, source: str, index: str, model: str = "text-embedding-3-small") -> "Embedding":
        raw_embedding: Dict[str, Any] = await Embedding.get_raw_embedding(content, model)
        embeddings: List[float] = raw_embedding["data"][0]["embedding"]

        return Embedding(
            source=source,
            content=content,
            index=index,
            embeddings=embeddings
        )

    @staticmethod
    async def query(query: str, index: str, model: str = "text-embedding-3-small", top_k: int = 10) -> List["Embedding"]:
        embedding_list: List[Embedding] = []
        query_embedding = await Embedding.get_embedding(content=query, source="query", index=index, model=model)
        async for session in database.get_async_session():
            stmt = (
                select(Vectors)
                .where(Vectors.index == index)
                .order_by(
                    func.l2_distance(Vectors.embedding, literal(query_embedding.embeddings, type_=Vectors.embedding.type))
                )
                .limit(top_k)
            )

            result = await session.execute(stmt)
            vectors = result.scalars().all()

            embedding_list = [
                Embedding(
                    id=str(vector.id),
                    source=vector.source,
                    content=vector.content,
                    index=vector.index,
                    embeddings=vector.embedding.tolist()
                )
                for vector in vectors
            ]

        return embedding_list


class EmbeddingGet(BaseModel):
    input: str
    model: str = Field(default="text-embedding-3-small")


class EmbeddingQuery(BaseModel):
    input: str
    index: str
    top_k: int = Field(default=10)
