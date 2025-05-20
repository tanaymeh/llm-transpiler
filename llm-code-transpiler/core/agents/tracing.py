from datetime import datetime
from pathlib import Path
from typing import List
from langchain_core.messages import BaseMessage
from loguru import logger
from core.state import State


class Tracer:
    """Handles tracing of agent conversations to console and files."""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.trace_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.trace_dir = Path(".traces")
        self.trace_file = self.trace_dir / f"{self.trace_id}_{self.agent_name}.txt"
        self.trace_dir.mkdir(parents=True, exist_ok=True)

    def log_interaction(self, messages: List[BaseMessage], response: str):
        """Log a single interaction to console and trace file."""
        # Console logging
        logger.debug(f"\n=== {self.agent_name} Trace ===")
        for msg in messages:
            logger.debug(f"{msg.type}: {msg.content}")
        logger.debug(f"AI Response: {response}")

        # File logging
        with open(self.trace_file, "a") as f:
            f.write(f"Time: {datetime.now().isoformat()}\n")
            f.write("== Messages ==\n")
            for msg in messages:
                f.write(f"{msg.type}: {msg.content}\n")
            f.write(f"\n== AI Response ==\n{response}\n")
            f.write("=" * 40 + "\n\n")


def with_tracing(func):
    """Decorator to add tracing to agent execution methods."""

    def wrapper(self, state: State) -> State:
        tracer = Tracer(self.name)
        # Get messages from the plan() call that happens in run()
        messages = self.plan(state)
        result = func(self, state)

        # Get the AI response from the last message or state
        ai_response = (
            getattr(state, "code", None)
            or getattr(state, "scratchpad", None)
            or "No response captured"
        )

        tracer.log_interaction(messages, ai_response)
        return result

    return wrapper
