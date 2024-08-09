import os
import json
from functools import partial

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

from typing import TypedDict

from dotenv import load_dotenv, find_dotenv

from conditions import compile_time_error
from nodes import transpile_node, compile_node, summary_node, format_node


class State(TypedDict):
    code: str
    original_code: str
    code_summary: str
    error: dict
    iterations: int


def init_graph(
    summary_node_fn,
    transpile_node_fn,
    compile_node_fn,
    format_node_fn,
    compile_time_error_fn,
):
    """Initialises the graph"""
    graph = StateGraph(State)

    # Add all the nodes
    graph.add_node("summary", summary_node_fn)
    graph.add_node("transpile", transpile_node_fn)
    graph.add_node("compile", compile_node_fn)
    graph.add_node("format", format_node_fn)

    # Set the entry point to be the transpile node
    graph.set_entry_point("summary")

    # Add edges
    graph.add_edge("summary", "transpile")
    graph.add_edge("transpile", "compile")
    graph.add_edge("format", END)

    # Add a conditional edge from compile to transpile if compilation failed
    graph.add_conditional_edges(
        "compile",
        compile_time_error_fn,
        {"terminate": "format", "continue": "transpile"},
    )

    return graph


if __name__ == "__main__":
    # Load the env secrets
    load_dotenv(find_dotenv())
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # Init the model and other parameters
    model_name = "gpt-4o-mini"
    is_debug = True
    max_iter = 3

    # Python file will have the same name as Java file but changed folder and extensions
    java_file_path = "dummy/java/LibraryManagementSystem.java"
    python_file_path = os.path.join(
        "dummy/python", os.path.basename(java_file_path).replace(".java", ".py")
    )

    model = ChatOpenAI(model=model_name, temperature=0.2, api_key=OPENAI_API_KEY)

    # Read in the original java code file
    with open(java_file_path, "r") as fl:
        java_code = fl.read()

    # Read the prompts
    with open("prompts.json", "r") as fl:
        prompts = json.load(fl)

    # Define an initial state
    state = State(
        code="",
        original_code=java_code,
        code_summary="",
        error={
            "status": 0,
            "message": "",
        },
        iterations=0,
    )

    # Define the partials for initialising the graph
    summary_node_fn = partial(summary_node, model=model, templates=prompts)
    transpile_node_fn = partial(transpile_node, model=model, templates=prompts)
    compile_node_fn = partial(compile_node, debug=is_debug)
    format_node_fn = partial(format_node, save_file_path=python_file_path)

    compile_time_error_fn = partial(compile_time_error, max_iter=max_iter)

    # Init the graph and compile it
    graph = init_graph(
        summary_node_fn,
        transpile_node_fn,
        compile_node_fn,
        format_node_fn,
        compile_time_error_fn,
    ).compile()

    # Run the graph
    graph.invoke(state)
