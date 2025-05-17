from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from core.state import State

from typing import cast


def generate_questions(model: ChatOpenAI, state: State, template: str) -> list:
    """Generates questions about a code file given a model, state and template"""
    messages = [
        SystemMessage(content=template.format(state.scratchpad)),
        HumanMessage(content=state.original_code),
    ]

    # Generate questions
    output = model(messages).content
    output = cast(str, output)
    questions: list[str] = output.split(".")

    return questions
