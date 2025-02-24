from enum import Enum
from functools import lru_cache
from typing import List, Dict, Any, Optional

import yaml
from langchain_openai.chat_models.base import ChatOpenAI
from pydantic import BaseModel

from src.common import Constants


class LLMConfig(BaseModel):
    name: str
    parent_model_id: str
    endpoint: Optional[str] = "https://api.openai.com/v1/"
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    developer_prompt: Optional[str] = "You are a helpful assistant."

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

    @staticmethod
    def _get_base_chat_model(llm_config: LLMConfig) -> ChatOpenAI:
        return ChatOpenAI(
            model=llm_config.parent_model_id,   #   type: ignore[call-arg]
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
                model=chat_model
            ))

        return sergeant_list

    @staticmethod
    def get(model_name: str) -> "Sergeant":
        return next(filter(lambda s: s.name == model_name, Sergeant.get_all()))

    @staticmethod
    def get_messages(request: BaseModel, sergeant: "Sergeant") -> List[Dict[str, str]]:
        message_list: List[Dict[str, str]] = []
        for message in request.messages:    #   type: ignore[attr-defined]
            is_developer_prompt = message.role == "system" or message.role == "developer"
            if is_developer_prompt:
                role: str = "developer"
                content: str = f"{sergeant.developer_prompt}\n---\n{message.content}"
            else:
                role = message.role
                content = message.content

            message_list.append({"role": role, "content": content})

        return message_list
