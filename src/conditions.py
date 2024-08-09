from typing import Any


def compile_time_error(state: Any, max_iter: int = 3):
    """If there was a compile time error, it takes the code back to transpile node"""
    if state["error"]["status"] == 0 or state["iterations"] > max_iter:
        return "terminate"
    else:
        return "continue"
