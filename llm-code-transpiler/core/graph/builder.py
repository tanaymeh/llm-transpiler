from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from core.state import State
from core.agents.base import Agent

from typing import Callable
from concurrent.futures import ThreadPoolExecutor


class GraphBuilder:
    """Factor for creating and configuring the transpilation graph"""

    def __init__(self):
        self._graph = StateGraph(state_schema=State)
        self._is_compiled = False

    def add_node(self, agent: Agent) -> None:
        """Adds an agent to the graph, wrapping its plan and execute steps"""
        self._graph.add_node(agent.name, agent.run)

    def add_edge(self, source: Agent, target: Agent) -> None:
        """Adds a direct edge from source agent to target agent"""
        self._graph.add_edge(source.name, target.name)

    def set_entry_point(self, node: Agent) -> None:
        """Sets a graph entry point"""
        self._graph.set_entry_point(node.name)

    def add_conditional_edge(
        self, source_node: Agent, condition: Callable, condition_map: dict
    ) -> None:
        """Adds a conditional edge to the graph between a source and single or multiple target nodes"""
        self._graph.add_conditional_edges(source_node.name, condition, condition_map)

    def compile(self) -> CompiledStateGraph:
        """Finalizes and returns the compiled graph"""
        # Compile the graph and wrap its invoke to support parallel execution
        compiled_graph = self._graph.compile()

        original_invoke = compiled_graph.invoke

        def invoke(state):
            # TODO: based on dependencies and dispatch independent agents in threads
            return original_invoke(state)

        compiled_graph.invoke = invoke  # type: ignore
        return compiled_graph
