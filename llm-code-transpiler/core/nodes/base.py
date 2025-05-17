from abc import ABC, abstractmethod
from typing import TypeVar, ParamSpec, Generic
from pydantic import Field
from langchain_openai import ChatOpenAI

P = ParamSpec("P")
R = TypeVar("R")


class Node(Generic[P, R], ABC):
    name: str
    model: ChatOpenAI
    system_prompt: str = Field(
        default_factory=lambda: "You are a helpful AI Agent that follows the instructions you are given"
    )
    _is_debug: bool

    @abstractmethod
    def func(self, *args: P.args, **kwargs: P.kwargs) -> R: ...
