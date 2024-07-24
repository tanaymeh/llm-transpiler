import os
import subprocess
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END

from typing import TypedDict, Union, List, Any

from utils import sanitize_output


# Define the State
# error here will be a dict with two
class State(TypedDict):
    code: str
    original_code: str
    error: dict
    iterations: int


SYSTEM_TEMPLATE = "You are an expert developer and you are tasked with transpiling code from Java to Python. Convert the given Java code into Python and make sure it's syntactically correct and does exactly what the Java code is doing. Also, make sure that the generated Python code follows best practices, is efficient, and uses standard libraries wherever possible. Don't generate any extra text, just the transpiled code.\n"


def transpile(
    state: State,
    model: Any,
    system_template: str,
    temperature: int = 0.3,
) -> State:
    """Transpile node"""
    # If there is no error, add the initial prompt and run the transpilation
    if not state["error"]["status"]:
        messages = [
            SystemMessage(content=system_template),
            HumanMessage(content=state["code"]),
        ]
    else:
        # If there was an error choose the human message based on the error code
        # Codes - 0 (no error), 1 (error compiling), 2 (compiles but the outputs don't match)
        error_messages = [AIMessage(content=state["code"])]
        # Program did not compile
        if state["error"]["status"] == 1:
            error_messages.append(
                HumanMessage(
                    content=f"The transpiled code you returned did not compile successfully. Following is the stack trace: {state['error']['message']}. Fix the error and return the working transpiled code. Don't generate any extra text, just the working transpiled code.\n"
                )
            )

        # Program compiled but the output wasn't working
        else:
            error_messages.append(
                HumanMessage(
                    content=f"The transpiled code you returned did compile but upon some tests, it's output was different than the output of the original code. Fix the transpiled code so that it's correct and does what the original code did. Here are more details about the test cases and the output they generated: {state['error']['message']} Don't generate any extra text, just the correct and working transpiled code.\n"
                )
            )

        # Add to the main messsages
        messages.extend(error_messages)

        # Get the output from model and clean it
        output = model.invoke(messages)
        output = sanitize_output(output.content)

        state["code"] = output
        state["iterations"] += 1
        return state
