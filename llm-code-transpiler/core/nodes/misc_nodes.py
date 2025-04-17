import os
import black
from loguru import logger

from .base import Node
from ..state import State, StateError


class PythonFormatNode(Node):
    """Formats Python code from a string"""

    def func(self, state: State) -> State:
        self.state = state
        logger.debug("Formatting Python code")

        mode = black.FileMode(string_normalization=False)
        self.state.code = black.format_str(state.code, fast=False, mode=mode)

        return self.state


class SaveCodeToDiskNode(Node):
    """Saves any code present in the state along with a provided name to the at the specified path"""

    target_name: str
    target_location: str

    def func(self, state: State) -> State:
        self.state: State = state
        full_path = os.path.join(self.target_location, self.target_name)
        with open(full_path, "w") as fl:
            fl.write(self.state.code)

        logger.debug(f"Saved code to disk at: {full_path}")

        return self.state
