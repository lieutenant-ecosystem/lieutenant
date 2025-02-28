import asyncio
import os
from typing import Optional, List, Any, Dict

import httpx
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from pydantic import BaseModel, Field
from sqlalchemy import make_url, create_engine, Engine, URL, text

from src import common

DEFAULT_MODEL: str = os.getenv("VECTOR_EMBEDDING_SERVICE_DEFAULT_MODEL") or "text-embedding-3-small"


def initialize_database():
    url: URL = make_url(os.getenv("VECTOR_EMBEDDING_SERVICE_DATABASE_URL"))
    database_name: str = url.database
    admin_url: URL = url.set(database="postgres")
    engine: Engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")

    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1 FROM pg_database WHERE datname=:dbname"), {"dbname": database_name})
        if not result.scalar():
            conn.execute(text(f"CREATE DATABASE \"{database_name}\""))


class Embedding(BaseModel):
    id: Optional[str] = None
    source: str
    content: str
    index: str
    embedding_model: Optional[str] = Field(default=DEFAULT_MODEL)

    def upsert(self) -> None:
        if self.id is None:
            self.id = common.get_sha256_hash(self.content)

        document: Document = Document(
            page_content=self.content,
            metadata=self.model_dump(exclude={"content"}),
        )

        vector_store = PGVector(
            embeddings=OpenAIEmbeddings(model=self.embedding_model),
            collection_name=self.index,
            connection=os.getenv("VECTOR_EMBEDDING_SERVICE_DATABASE_URL"),
            use_jsonb=True,
        )

        #   TODO: Figure out why "Failed to create vector extension: greenlet_spawn has not been called; can't call await_only() here. Was IO attempted in an unexpected place?" and make this asynchronous
        # await asyncio.to_thread(vector_store.add_documents, [document], ids=[document.metadata["id"]])
        vector_store.add_documents([document], ids=[document.metadata["id"]])

    @staticmethod
    def query(query: str, index: str, model: Optional[str] = None, k: int = 10) -> List["Embedding"]:
        model = DEFAULT_MODEL if model is None else model
        vector_store = PGVector(
            embeddings=OpenAIEmbeddings(model=model),
            collection_name=index,
            connection=os.getenv("VECTOR_EMBEDDING_SERVICE_DATABASE_URL"),
            use_jsonb=True,
        )

        #   TODO: Figure out why "Failed to create vector extension: greenlet_spawn has not been called; can't call await_only() here. Was IO attempted in an unexpected place?" and make this asynchronous
        # document_list: List[Document] = await asyncio.to_thread(vector_store.similarity_search, query, k=k)
        document_list: List[Document] = vector_store.similarity_search(query, k=k)

        return [Embedding(
            id=document.id,
            source=document.metadata.get("source"),
            content=document.page_content,
            index=index,
            embedding_model=model
        ) for document in document_list]

    @staticmethod
    async def get_raw_embedding(content: str, model: Optional[str] = None) -> Dict[str, Any]:
        model = DEFAULT_MODEL if model is None else model
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


class EmbeddingGet(BaseModel):
    input: str
    model: str = Field(default="text-embedding-3-small")


class EmbeddingQuery(BaseModel):
    input: str
    index: str
    top_k: int = Field(default=10)


initialize_database()
