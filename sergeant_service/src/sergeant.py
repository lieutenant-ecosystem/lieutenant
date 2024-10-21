from enum import Enum
from functools import lru_cache
from typing import List, Dict, Any, Optional

import yaml
from langchain_openai.chat_models.base import BaseChatOpenAI
from pydantic import BaseModel

from src.common import Constants


class LLM(Enum):
    GPT_4O_MINI: str = "GPT-4o Mini"
    GPT_4O: str = "GPT-4o"
    O1_PREVIEW: str = "o1 Preview"
    O1_MINI: str = "o1 Mini"


class LLMConfig(BaseModel):
    name: str
    id: str
    temperature: Optional[float] = 0.2
    max_tokens: Optional[int] = 4096
    system_prompt: Optional[str] = "You are a helpful assistant."

    @staticmethod
    def get_all() -> List["LLMConfig"]:
        with open(Constants.LLM_YAML_PATH.value, "r") as raw_string:
            raw_data_list: List[Dict[str, Any]] = yaml.safe_load(raw_string)

        return [LLMConfig(**raw_data) for raw_data in raw_data_list]


class Sergeant(BaseModel):
    llm: LLM
    model: BaseChatOpenAI

    @staticmethod
    @lru_cache
    def get_all() -> List["Sergeant"]:
        return [Sergeant(
            llm=next(filter(lambda l: l.value == llm_config.name, list(LLM))),
            model=BaseChatOpenAI(
                temperature=llm_config.temperature,
                max_tokens=llm_config.max_tokens,
                model=llm_config.id
            )
        ) for llm_config in LLMConfig.get_all()]

    @staticmethod
    def get(llm: LLM) -> "Sergeant":
        return next(filter(lambda s: s.llm == llm, Sergeant.get_all()))
