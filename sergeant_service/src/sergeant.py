import json
import os
import time
import uuid
from functools import lru_cache
from typing import List, Dict, Any, Optional, AsyncGenerator

import yaml
from langchain.retrievers import SelfQueryRetriever, MergerRetriever
from langchain_core.documents import Document
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


class LLMIndexConfig(BaseModel):
    id: str
    description: str


class LLMConfig(BaseModel):
    name: str
    parent_model_id: str
    endpoint: Optional[str] = "https://api.openai.com/v1/"
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    developer_prompt: str = "You are a helpful assistant."
    index_list: List[LLMIndexConfig] = []
    api_key_environment_variable_key: Optional[str] = None

    @staticmethod
    def get_all() -> List["LLMConfig"]:
        llm_config_list: List[LLMConfig] = []
        with open(Constants.LLM_YAML_PATH.value, "r") as raw_string:
            raw_data_list: List[Dict[str, Any]] = yaml.safe_load(raw_string)

        for raw_data in raw_data_list:
            name: str = raw_data.get("name")
            parent_model_id: str = raw_data.get("parent_model_id")
            endpoint: str = raw_data.get("endpoint") or "https://api.openai.com/v1/"
            temperature: int = raw_data.get("temperature")
            max_tokens: int = raw_data.get("max_tokens")
            api_key_environment_variable_key: str = raw_data.get("api_key_environment_variable_key")
            developer_prompt: str = raw_data.get("developer_prompt") or "You are a helpful assistant."
            index_list: List[LLMIndexConfig] = [LLMIndexConfig(**index_config) for index_config in raw_data.get("indexes")] if raw_data.get("indexes") is not None else []

            llm_config_list.append(LLMConfig(
                name=name,
                parent_model_id=parent_model_id,
                endpoint=endpoint,
                temperature=temperature,
                max_tokens=max_tokens,
                developer_prompt=developer_prompt,
                index_list=index_list,
                api_key_environment_variable_key=api_key_environment_variable_key
            ))

        return llm_config_list


class Sergeant(BaseModel):
    name: str
    parent_model_id: str
    developer_prompt: str
    model: ChatOpenAI
    llm_config: LLMConfig

    def add_context_from_indexes(self, messages: List[Dict[str, str]]) -> None:
        retrievers_list: List[SelfQueryRetriever] = []

        for index in self.llm_config.index_list:
            vector_store = PGVector(
                embeddings=OpenAIEmbeddings(model=DEFAULT_EMBEDDING_MODEL),
                collection_name=index.id,
                connection=os.getenv("VECTOR_EMBEDDING_SERVICE_DATABASE_URL"),
                use_jsonb=True,
            )
            retriever: SelfQueryRetriever = SelfQueryRetriever.from_llm(self.model, vector_store, index.description, metadata_field_info=[], verbose=True)
            retrievers_list.append(retriever)

        parent_retriever: MergerRetriever = MergerRetriever(retrievers=retrievers_list)

        query: str = messages[-1]["content"]
        retrieved_docs: List[Document] = parent_retriever.invoke(query)
        if len(retrieved_docs) > 0:
            context: str = ""
            for document in retrieved_docs:
                context = context + "# Data\n"
                context = context + f"{document.page_content}"
                context = context + "# Metadata\n"
                context = context + f"## Source\nf{document.metadata.get("source")}"

            messages.insert(0, {"role": "system", "content": f"{self.developer_prompt}\n---\n# Context retrieved\n{context}"})

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
            max_tokens=llm_config.max_tokens,
            base_url=llm_config.endpoint or os.getenv("OPENAI_COMPATIBLE_API_BASE_URL"),
            api_key=os.getenv(llm_config.api_key_environment_variable_key) if llm_config.api_key_environment_variable_key else os.getenv("OPENAI_COMPATIBLE_API_KEY")
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
                llm_config=llm_config
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
                role: str = "user" if "o1" in str(request.model).lower() or "reason" in str(request.model).lower() else "system"  # TODO: This is a known bug with o1-mini
                content: str = f"{sergeant.developer_prompt}\n---\n{message.content}"
            else:
                role = message.role
                content = message.content

            message_list.append({"role": role, "content": content})

        return message_list
