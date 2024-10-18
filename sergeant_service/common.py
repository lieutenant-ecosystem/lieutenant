import os
from enum import Enum


class Constants(Enum):
    DATA_PATH: str = f"data/"
    LLM_YAML_PATH: str = f"{DATA_PATH}llm.yml"


def is_production_environment() -> bool:
    return os.environ.get('ENVIRONMENT') == 'production'


def is_test_environment() -> bool:
    return not is_production_environment()
