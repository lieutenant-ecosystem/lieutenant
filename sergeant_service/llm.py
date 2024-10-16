from enum import Enum

from langchain_openai.chat_models.base import BaseChatOpenAI
from pydantic import BaseModel


class LLM(BaseModel):
    name: str
    model: BaseChatOpenAI


class LLMEnum(Enum):
    GPT_4O_MINI: LLM = LLM(name="GPT-4o Mini", model=BaseChatOpenAI(temperature=0.2, max_tokens=4096, model_name="gpt-4o-mini"))
