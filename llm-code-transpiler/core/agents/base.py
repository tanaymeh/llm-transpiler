from abc import ABC, abstractmethod
from typing import TypeVar, ParamSpec, Generic, Any
from pydantic import BaseModel, Field
from core.state import State
from langchain_openai import ChatOpenAI

P = ParamSpec("P")
R = TypeVar("R")


class Agent(BaseModel, Generic[P, R], ABC):
    name: str
    model: ChatOpenAI
    system_prompt: str = Field(
        default_factory=lambda: "You are a helpful AI Agent that follows the instructions you are given. You have access to a scratchpad: {}"
    )

    @abstractmethod
    def plan(self, *args: P.args, **kwargs: P.kwargs) -> R:
        """
        Generate a plan for the agent's execute step.
        """
        ...

    @abstractmethod
    def execute(self, *args: P.args, **kwargs: P.kwargs) -> R:
        """
        Execute the agent's action based on its plan.
        """
        ...

    @abstractmethod
    def run(self, state: State) -> State:
        """
        Binds the planning and execution stage of an Agent to expose to GraphBuilder
        """
        ...
