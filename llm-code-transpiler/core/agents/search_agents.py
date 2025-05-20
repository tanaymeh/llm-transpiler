from loguru import logger
from core.agents.base import Agent
from core.state import State

from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_core.messages import SystemMessage, HumanMessage

from typing import cast


class SearchAgent(Agent):
    """
    Searches internet for context when there was an error, generating Q&A pairs.
    WIP
    """

    name: str = "search"
    search_agent_prompt: str

    def plan(self, state: State) -> list[str]:
        """
        Search the internet based on the errors encountered and then return a list of error-solution pairs
        """
        messages = [
            SystemMessage(content=self.search_agent_prompt.format(state.scratchpad)),
            HumanMessage(content=state.original_code),
        ]

        # Generate questions
        output = self.model(messages).content
        output = cast(str, output)
        questions: list[str] = output.split(".")

        return questions

    def execute(self, state: State, questions: list[str]) -> State:
        """
        Execute search based on last error; appends Q&As to state.scratchpad.
        """
        logger.debug("Running the SearchAgent")

        searcher = GoogleSerperAPIWrapper()
        for idx, ques in enumerate(questions):
            ans: str = searcher.run(ques)
            state.scratchpad += f"Question {idx}: {ques}\nAnswer: {ans}\n\n"

        return state

    def run(self, state: State) -> State:
        """Binds the planning and execution part together"""
        if state.last_error.status == 0:
            logger.debug("No error detected; skipping search")
            return state

        solutions = self.plan(state)
        self.state = self.execute(state, solutions)
        return self.state
