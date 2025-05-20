from loguru import logger
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from core.agents.tracing import with_tracing

from core.state import State
from core.agents.base import Agent
from core.agents.utils import sanitize_output, python_compile


class TranspileAgent(Agent):
    """
    Handles transpilation task based on the last error status.
    """

    name: str = "transpile"
    transpile_user_prompt: str
    error_prompts: dict[int | str, str]

    def plan(self, state: State) -> list[BaseMessage]:
        """
        Planning in TranspileAgent is just forming the messages based on the previous error status
        """
        messages: list[BaseMessage] = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(
                content=self.transpile_user_prompt.format(
                    plan=state.scratchpad, original_code=state.original_code
                )
            ),
        ]

        # If there was an error, include previous code and the error message
        if state.last_error.status != 0:
            error_messages = [
                AIMessage(
                    content=state.code
                ),  # Since the faulty code was agent generated
                HumanMessage(
                    content=self.error_prompts[state.last_error.status].format(
                        code=state.code, trace=state.last_error.message
                    )
                ),
            ]
            messages.extend(error_messages)

        return messages

    def execute(self, state: State, messages: list[BaseMessage]) -> State:
        """
        Execute the transpilation LLM call based on the last error status.
        """
        logger.debug(
            f"Last error status: {state.last_error.status} | current iter: {state.current_iterations}"
        )

        # Get the outputs from the model
        output: AIMessage = self.model.invoke(messages)  # type: ignore
        output_str = sanitize_output(output)

        state.code = output_str
        state.current_iterations += 1

        # Once we have the output, we see if it compiles or not
        state.last_error = python_compile(state.code)

        return state

    @with_tracing
    def run(self, state: State) -> State:
        """Binds the planning and execution part together"""
        messages = self.plan(state)
        return self.execute(state, messages)


class SummaryAgent(Agent):
    """
    Generates a summary of the original code file.
    """

    name: str = "summary"
    summary_user_prompt: str

    def plan(self, state: State) -> list[BaseMessage]:
        """
        Planning here is just forming the messages
        """
        messages: list[BaseMessage] = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(
                content=self.summary_user_prompt.format(source_code=state.original_code)
            ),
        ]

        return messages

    def execute(self, state: State, messages: list[BaseMessage]) -> State:
        """
        Execute the summary LLM call.
        """
        logger.debug("Running the SummaryAgent")
        output: AIMessage = self.model.invoke(messages)  # type: ignore
        output_str = sanitize_output(output)

        # Store the summary in the state scratchpad
        state.scratchpad = output_str
        return state

    def run(self, state: State) -> State:
        """Binds the planning and execution part together"""
        messages = self.plan(state)
        return self.execute(state, messages)


class PlanningAgent(Agent):
    """
    Generates a step-by-step plan on how to transpile any given code.
    """

    name: str = "planning"
    planning_user_prompt: str

    def plan(self, state: State) -> list[BaseMessage]:
        """
        Execute the planning LLM call to generate a detailed plan.
        """
        messages: list[BaseMessage] = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(
                content=self.planning_user_prompt.format(
                    summary=state.scratchpad, original_code=state.original_code
                )
            ),
        ]
        return messages

    def execute(self, state: State, messages: list[BaseMessage]) -> State:
        """
        Apply the generated plan to the state scratchpad.
        """
        logger.debug("Running the PlanningAgent")

        output: AIMessage = self.model.invoke(messages)  # type: ignore
        output_str = sanitize_output(output)
        state.scratchpad = output_str

        return state

    def run(self, state: State) -> State:
        """Binds the planning and execution part together"""
        messages = self.plan(state)
        return self.execute(state, messages)
