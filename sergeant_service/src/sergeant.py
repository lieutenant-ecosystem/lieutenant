import json
import os
import time
import uuid
from functools import lru_cache
from typing import List, Dict, Any, Optional, AsyncGenerator

import yaml
from langchain.retrievers import SelfQueryRetriever, MergerRetriever
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_openai import OpenAIEmbeddings
from langchain_openai.chat_models.base import ChatOpenAI
from langchain_postgres import PGVector
from pydantic import BaseModel
from starlette.responses import StreamingResponse

from src.common import Constants
from src.models import ChatCompletionRequest, ChatCompletionResponse

DEFAULT_EMBEDDING_MODEL: str = os.getenv("VECTOR_EMBEDDING_SERVICE_DEFAULT_MODEL") or "text-embedding-3-small"


async def stream_response(llm: BaseChatModel, messages: List[Dict], request: ChatCompletionRequest) -> AsyncGenerator[str, None]:
    async for chunk in llm.astream(messages):
        token = chunk.content
        if token:
            yield f"data: {json.dumps({
                'id': str(uuid.uuid4()),
                'object': 'chat.completion.chunk',
                'created': int(time.time()),
                'model': request.model,
                'choices': [{'delta': {'content': token}}],
            })}\n\n"
    yield "data: [DONE]\n\n"


class LLMConfig(BaseModel):
    name: str
    parent_model_id: str
    endpoint: Optional[str] = "https://api.openai.com/v1/"
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    developer_prompt: Optional[str] = "You are a helpful assistant."
    indexes: List[str] = []

    @staticmethod
    def get_all() -> List["LLMConfig"]:
        with open(Constants.LLM_YAML_PATH.value, "r") as raw_string:
            raw_data_list: List[Dict[str, Any]] = yaml.safe_load(raw_string)

        return [LLMConfig(**raw_data) for raw_data in raw_data_list]


class Sergeant(BaseModel):
    name: str
    parent_model_id: str
    developer_prompt: str
    model: ChatOpenAI
    indexes: List[str] = []

    def add_context_from_indexes(self, messages: List[Dict[str, str]]) -> None:
        retrievers_list: List[SelfQueryRetriever] = []
        for index_name in self.indexes:
            index_description: str = "Capitals of different countries"
            retrievers_list.append(
                SelfQueryRetriever.from_llm(
                    self.model,
                    PGVector(
                        embeddings=OpenAIEmbeddings(model=DEFAULT_EMBEDDING_MODEL),
                        collection_name=index_name,
                        connection=os.getenv("VECTOR_EMBEDDING_SERVICE_DATABASE_URL"),
                        use_jsonb=True,
                    ),
                    index_description,
                    metadata_field_info=[],
                    verbose=True,
                )
            )

        parent_retriever: MergerRetriever = MergerRetriever(retrievers=retrievers_list)

        query: str = messages[-1]["content"]
        retrieved_docs = parent_retriever.get_relevant_documents(query)
        if len(retrieved_docs) > 0:

            #   TODO: Add more context from metadata here
            docs_context = "\n---\n".join([doc.page_content for doc in retrieved_docs])
            messages.insert(0, {"role": "system", "content": f"Retrieved Context:\n{docs_context}"})

    async def ask(self, messages: List[Dict[str, str]]) -> ChatCompletionResponse:
        response: BaseMessage = await self.model.ainvoke(messages)
        return ChatCompletionResponse.get(response)

    def ask_stream(self, messages: List[Dict[str, str]], request: ChatCompletionRequest) -> StreamingResponse:
        return StreamingResponse(stream_response(self.model, messages, request), media_type="text/event-stream")

    @staticmethod
    def _get_base_chat_model(llm_config: LLMConfig) -> ChatOpenAI:
        return ChatOpenAI(
            model=llm_config.parent_model_id,
            temperature=llm_config.temperature,
            max_tokens=llm_config.max_tokens
        )

    @staticmethod
    @lru_cache
    def get_all() -> List["Sergeant"]:
        sergeant_list: List[Sergeant] = []
        for llm_config in LLMConfig.get_all():
            chat_model: ChatOpenAI = Sergeant._get_base_chat_model(llm_config)

            sergeant_list.append(Sergeant(
                name=llm_config.name,
                parent_model_id=llm_config.parent_model_id,
                developer_prompt=llm_config.developer_prompt,
                model=chat_model,
                indexes=llm_config.indexes
            ))

        return sergeant_list

    @staticmethod
    def get(model_name: str) -> "Sergeant":
        return next(filter(lambda s: s.name == model_name, Sergeant.get_all()))

    @staticmethod
    def get_messages(request: BaseModel, sergeant: "Sergeant") -> List[Dict[str, str]]:
        message_list: List[Dict[str, str]] = []
        for message in request.messages:  # type: ignore[attr-defined]
            is_developer_prompt = message.role == "system" or message.role == "developer"
            if is_developer_prompt:
                role: str = "developer"
                content: str = f"{sergeant.developer_prompt}\n---\n{message.content}"
            else:
                role = message.role
                content = message.content

            message_list.append({"role": role, "content": content})

        return message_list
