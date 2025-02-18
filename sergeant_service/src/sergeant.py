from enum import Enum
from functools import lru_cache
from typing import List, Dict, Any, Optional

import yaml
from langchain_anthropic import ChatAnthropic
from langchain_community.chat_models import ChatPerplexity
from langchain_core.language_models import BaseChatModel
from langchain_openai.chat_models.base import BaseChatOpenAI
from pydantic import BaseModel

from src.common import Constants


class LLM(Enum):
    GPT_4O_MINI: str = "GPT-4o Mini"
    GPT_4O: str = "GPT-4o"
    O1_PREVIEW: str = "o1 Preview"
    O1_MINI: str = "o1 Mini"
    CLAUDE_35_SONNET: str = "Claude 3.5 Sonnet"
    LLAMA_31_SONAR_8B: str = "Llama 3.1 Sonar 8B"
    LLAMA_31_SONAR_70B: str = "Llama 3.1 Sonar 70B"
    LLAMA_31_8B: str = "Llama 3.1 8B"
    LLAMA_31_70B: str = "Llama 3.1 70B"


class LLMCompatibility(Enum):
    OPEN_AI: str = "OpenAI"
    ANTHROPIC: str = "Anthropic"
    PERPLEXITY: str = "Perplexity"


class LLMConfig(BaseModel):
    name: str
    id: str
    compatibility: LLMCompatibility
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
    model: BaseChatModel

    @staticmethod
    @lru_cache
    def get_all() -> List["Sergeant"]:
        sergeant_list: List[Sergeant] = []
        for llm_config in LLMConfig.get_all():
            if llm_config.compatibility == LLMCompatibility.OPEN_AI:
                model_class: type = BaseChatOpenAI
            elif llm_config.compatibility == LLMCompatibility.ANTHROPIC:
                model_class: type = ChatAnthropic
            else:
                model_class: type = ChatPerplexity

            llm: LLM = next(filter(lambda l: l.value == llm_config.name, list(LLM)))

            sergeant_list.append(Sergeant(
                llm=llm,
                model=model_class(
                    temperature=llm_config.temperature,
                    max_tokens=llm_config.max_tokens,
                    model=llm_config.id
                )
            ))

        return sergeant_list

    @staticmethod
    def get(llm: LLM) -> "Sergeant":
        return next(filter(lambda s: s.llm == llm, Sergeant.get_all()))
