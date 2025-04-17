from loguru import logger

from .base import Node
from ..state import State, StateError
from ..utils import generate_questions

from langchain_community.utilities import GoogleSerperAPIWrapper

from dotenv import load_dotenv


class SearchNode(Node):
    """Generates questions on how to tranliterate certain parts of the code then searches the internet for the context"""

    def func(self, state: State) -> State:
        _ = load_dotenv()
        self.state = state
        logger.debug("Generating questions")

        searcher = GoogleSerperAPIWrapper()
        questions: list = generate_questions(
            self.model, self.state, template=self.system_prompt
        )
        for idx, ques in enumerate(questions):
            ans: str = searcher.run(ques)
            self.state.scratchpad += (
                f"Question {idx}." + ques + "\nAnswer:" + ans + "\n\n"
            )

        return state
