import json
import black
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from typing import Any

from utils import sanitize_output, python_compile


def transpile_node(
    state: Any,
    model: Any,
    templates: dict,
) -> Any:
    """
    Transpile Node that handles the main transpiling task based on the error status
    """
    print(f"[DEBUG]: Transpiling code, iter: {state['iterations']}")

    # If there is no error, add the initial prompt and run the transpilation
    if state["error"]["status"] == 0:
        messages = [
            SystemMessage(content=templates["transpile"].format(state["code_summary"])),
            HumanMessage(content=state["original_code"]),
        ]

    else:
        messages = [
            SystemMessage(content=templates["transpile"].format(state["code_summary"])),
            HumanMessage(content=state["original_code"]),
        ]

        # If there was an error choose the human message based on the error code
        # Codes - 0 (no error), 1 (error compiling), 2 (compiles but the outputs don't match)
        error_messages = [AIMessage(content=state["code"])]

        # Program did not compile
        if state["error"]["status"] == 1:
            error_messages.append(
                HumanMessage(
                    content=templates["transpile_compile_err"].format(
                        state["error"]["message"]
                    )
                )
            )

        # Program compiled but the output wasn't working
        else:
            error_messages.append(
                HumanMessage(
                    content=templates["templates_output_err"].format(
                        state["error"]["message"]
                    )
                )
            )

        # Add to the main messsages
        messages.extend(error_messages)

    # Some debug messages
    print(
        f"[DEBUG] transpile status: {'no error' if not state['error']['status'] else 'compile time error'}, curr_iter: {state['iterations']}"
    )

    # Get the output from model and clean it
    output = model.invoke(messages)
    output = sanitize_output(output.content)

    state["code"] = output
    state["iterations"] += 1
    return state


def compile_node(state: Any, debug: bool = True) -> Any:
    """
    Compile node that parses the Python code using AST and returns a state with error status and messages (if any)
    """
    print("[DEBUG]: Compiling Code")

    code = state["code"]
    state["error"] = python_compile(code, state["error"])

    return state


def summary_node(state: Any, model: Any, templates: dict) -> Any:
    """Generates summary of the original code file"""
    print("[DEBUG]: Generating Code summary")
    messages = [
        SystemMessage(content=templates["summary"]),
        HumanMessage(content=state["original_code"]),
    ]

    # Get the output from model and clean it
    output = model.invoke(messages)
    state["code_summary"] = output.content

    return state


def format_node(state: Any, save_file_path: str) -> Any:
    """Formats the code using Black to match PEP8 standards"""
    print("[DEBUG] Formatting the code")

    mode = black.FileMode(string_normalization=False)
    state["code"] = black.format_file_contents(state["code"], fast=False, mode=mode)

    with open(save_file_path, "w") as fl:
        fl.write(state["code"])

    print(f"[DEBUG] Formatted code file saved to disk at: '{save_file_path}'")
    return state
