from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from ..state import State


def generate_questions(model: ChatOpenAI, state: State, template: str) -> list:
    """Generates questions about a code file given a model, state and template"""
    messages = [
        SystemMessage(content=template.format(state["scratchpad"])),
        HumanMessage(content=state["original_code"]),
    ]

    # Generate questions
    questions: list[str] = model(messages).content.split(".")

    return questions
