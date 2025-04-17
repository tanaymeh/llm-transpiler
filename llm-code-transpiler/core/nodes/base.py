from typing import Any
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI


class Node(BaseModel):
    model: ChatOpenAI
    system_prompt: str = Field(
        default_factory="You are a helpful AI Agent that follows are instructions you are given"
    )
    _is_debug: bool

    def func(self, **kwargs) -> Any:
        pass
