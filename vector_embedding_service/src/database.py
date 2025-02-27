import os
import uuid
from typing import AsyncGenerator

from pgvector.sqlalchemy import Vector  # Ensure pgvector is installed
from sqlalchemy import Column, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

#   TODO: Add logic that automatically creates the database if it doesn't exist
Base = declarative_base()
engine = create_async_engine(f"postgresql+asyncpg://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@10.1.83.27:5432/lieutenant-vector_embedding_service", echo=True)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore[call-overload]


async def create_vector_extension() -> None:
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))


async def init_db() -> None:
    async with engine.begin() as conn:
        await create_vector_extension()
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session() -> AsyncGenerator:
    await init_db()
    async with AsyncSessionLocal() as session:
        yield session


class Vectors(Base):  # type: ignore[misc,valid-type]
    __tablename__ = 'vectors'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content = Column(String, nullable=False)
    source = Column(String, nullable=False)
    index = Column(String, nullable=False)
    embedding = Column(Vector(1536), nullable=False)  # type: ignore[var-annotated]
