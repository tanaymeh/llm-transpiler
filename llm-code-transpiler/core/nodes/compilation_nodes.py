from loguru import logger

from nodes.base import Node
from core.state import State
from core.utils import python_compile


class PythonCompileNode(Node):
    """Tries to compile Python code using AST"""

    def func(self, state: State) -> State:
        self.state: State = state
        logger.debug("Compiling Python code")

        self.state.last_error = python_compile(self.state.code)
        return self.state
