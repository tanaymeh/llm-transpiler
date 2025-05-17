from loguru import logger
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage

from core.nodes.base import Node
from core.state import State
from core.utils import sanitize_output


class TranspileNode(Node):
    """Handles transpilation task based on the last error status"""

    scratchpad: str
    transpile_prompt: str
    error_prompts: dict[int | str, str]

    def consolidate_chat_history(self) -> list[BaseMessage]:
        """
        Consolidates the chat history in a list to be passed into the model
        """
        messages: list = [
            SystemMessage(content=self.system_prompt.format(self.scratchpad)),
            HumanMessage(
                content=self.transpile_prompt.format(self.state.original_code)
            ),
        ]
        # If there was error in previous transpilation
        if self.state.last_error.status != 0:
            error_messages: list[BaseMessage] = [AIMessage(content=self.state.code)]

            # Get the error prompt based on the error status code
            error_message = HumanMessage(
                content=self.error_prompts[self.state.last_error.status].format(
                    self.state.last_error.message
                )
            )
            error_messages.append(error_message)

            messages.extend(error_messages)

        return messages

    def func(self, state: State) -> State:
        self.state: State = state

        logger.debug(
            f"Last error status: {self.state.last_error.status} | current iter: {self.state.current_iterations}"
        )

        # Get the model generation
        messages: list[BaseMessage] = self.consolidate_chat_history()
        output: AIMessage = self.model.invoke(messages)  # type: ignore
        output_str = sanitize_output(output)
        # Update the state
        self.state.code = output_str
        self.state.current_iterations += 1
        return self.state


class SummaryNode(Node):
    """Generates summary of original code file"""

    summary_prompt: str

    def func(self, state: State) -> State:
        self.state: State = state

        logger.debug("Generating a summary of the original code")

        # Form the history
        messages: list[BaseMessage] = [
            SystemMessage(content=self.system_prompt.format(self.state.scratchpad)),
            HumanMessage(content=self.summary_prompt.format(self.state.original_code)),
        ]

        # Get the summary from the model
        output: AIMessage = self.model.invoke(messages)  # type: ignore
        output_str = sanitize_output(output)
        self.state.scratchpad = output_str

        return self.state


class PlanningNode(Node):
    """Generated a step by step plan on how to transpile any given code"""

    planning_prompt: str

    def func(self, state: State) -> State:
        self.state: State = state
        logger.debug("Generating a step by step plan on how to transpile")

        # Form the history
        messages: list[BaseMessage] = [
            SystemMessage(content=self.system_prompt.format(self.state.scratchpad)),
            HumanMessage(content=self.planning_prompt.format(self.state.original_code)),
        ]

        # Get the plan from the model
        output: AIMessage = self.model.invoke(messages)  # type: ignore
        output_str = sanitize_output(output)
        self.state.scratchpad = output_str

        return self.state
