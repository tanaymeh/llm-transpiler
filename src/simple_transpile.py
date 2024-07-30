import os
from functools import partial

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END

from typing import TypedDict, Any

from utils import sanitize_output, python_compile

from dotenv import load_dotenv, find_dotenv


class State(TypedDict):
    code: str
    original_code: str
    error: dict
    iterations: int


def transpile_node(
    state: State,
    model: Any,
    system_template: str,
) -> State:
    """
    Transpile node
    This node both transpiles a code for the first time and optimises the code if it didn't work as intended or failed to compile
    """
    # If there is no error, add the initial prompt and run the transpilation
    if state["error"]["status"] == 0:
        messages = [
            SystemMessage(content=system_template),
            HumanMessage(content=state["original_code"]),
        ]

    else:
        messages = [
            SystemMessage(content=system_template),
            HumanMessage(content=state["original_code"]),
        ]

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


def compile_node(
    state: State, debug: bool = True, save_file_path: str = "dummy/test_file.py"
):
    """
    Compilation Node
    This node compiles transpiled code and if there were any errors during compilation it updates the state
    """
    code = state["code"]
    state["error"] = python_compile(code, state["error"])
    if debug:
        # In debugging mode, save the file to the disk even with error
        with open(f"{save_file_path}", "w") as fl:
            print(f"[DEBUG] File saved to disk at: '{save_file_path}'")
            fl.write(code)
    else:
        if state["error"]["status"] == 0:
            with open(f"{save_file_path}", "w") as fl:
                fl.write(code)

    return state


def compile_time_error(state: State, max_iter: int = 3):
    """If there was a compile time error, it takes the code back to transpile node"""
    if state["error"]["status"] == 0 or state["iterations"] > max_iter:
        return "terminate"
    else:
        return "continue"


def init_graph(transpile_node_fn, compile_node_fn, compile_time_error_fn):
    """Initialises the graph"""
    graph = StateGraph(State)

    # Add all the nodes
    graph.add_node("transpile", transpile_node_fn)
    graph.add_node("compile", compile_node_fn)

    # Set the entry point to be the transpile node
    graph.set_entry_point("transpile")

    # Add edge from transpile to compile node
    graph.add_edge("transpile", "compile")

    # Add a conditional edge from compile to transpile if compilation failed
    graph.add_conditional_edges(
        "compile",
        compile_time_error_fn,
        {"terminate": END, "continue": "transpile"},
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
    java_file_path = "dummy/java/CandyLCHard.java"
    python_file_path = os.path.join(
        "dummy/python", os.path.basename(java_file_path).replace(".java", ".py")
    )

    SYSTEM_TEMPLATE = "You are an expert developer and you are tasked with transpiling code from Java to Python. Convert the given Java code into Python and make sure it's syntactically correct and does exactly what the Java code is doing. Also, make sure that the generated Python code follows best practices, is efficient, and uses standard libraries wherever possible. Don't generate any extra text, just the transpiled code.\n"

    model = ChatOpenAI(model=model_name, temperature=0.2, api_key=OPENAI_API_KEY)

    # Read in the original java code file
    with open(java_file_path, "r") as fl:
        java_code = fl.read()

    # Define an initial state
    state = State(
        code="",
        original_code=java_code,
        error={
            "status": 0,
            "message": "",
        },
        iterations=0,
    )

    # Define the partials for initialising the graph
    transpile_node_fn = partial(
        transpile_node, model=model, system_template=SYSTEM_TEMPLATE
    )

    compile_node_fn = partial(
        compile_node, debug=is_debug, save_file_path=python_file_path
    )

    compile_time_error_fn = partial(compile_time_error, max_iter=max_iter)

    # Init the graph and compile it
    graph = init_graph(
        transpile_node_fn, compile_node_fn, compile_time_error_fn
    ).compile()

    # Run the graph
    graph.invoke(state)
