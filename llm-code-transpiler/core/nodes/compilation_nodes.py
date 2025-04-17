from loguru import logger

from .base import Node
from ..state import State
from ..utils import python_compile


class PythonCompileNode(Node):
    """Tries to compile Python code using AST"""

    def func(self, state: State) -> State:
        self.state: State = state
        logger.debug("Compiling Python code")

        self.state.last_error = python_compile(self.state.code)
        return self.state
