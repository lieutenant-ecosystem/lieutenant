from enum import Enum

from langchain_openai.chat_models.base import BaseChatOpenAI
from pydantic import BaseModel


class LLM(BaseModel):
    name: str
    model: BaseChatOpenAI


class LLMEnum(Enum):
    GPT_4O_MINI: LLM = LLM(name="GPT-4o Mini", model=BaseChatOpenAI(temperature=0.2, max_tokens=4096, model_name="gpt-4o-mini"))
    GPT_4O: LLM = LLM(name="GPT-4o", model=BaseChatOpenAI(temperature=0.2, max_tokens=4096, model_name="chatgpt-4o-latest"))
    O1_PREVIEW: LLM = LLM(name="o1 Preview", model=BaseChatOpenAI(temperature=0.2, max_tokens=4096, model_name="o1-preview"))
    O1_MINI: LLM = LLM(name="o1 Mini", model=BaseChatOpenAI(temperature=0.2, max_tokens=4096, model_name="o1-mini"))
