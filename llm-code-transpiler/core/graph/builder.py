from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from core.state import State
from core.nodes import Node

from typing import Callable


class GraphBuilder:
    """Factor for creating and configuring the transpilation graph"""

    def __init__(self):
        self._graph = StateGraph(state_schema=State)
        self._is_compiled = False

    def add_node(self, name: str, node: Node) -> None:
        """Adds a node to the graph"""
        self._graph.add_node(node.name, node.func)  # type: ignore

    def set_entry_point(self, node: Node) -> None:
        """Sets a graph entry point"""
        self._graph.set_entry_point(node.name)

    def add_conditional_edge(
        self, source_node: Node, condition: Callable, condition_map: dict
    ) -> None:
        """Adds a conditional edge to the graph between a source and single or multiple target nodes"""
        self._graph.add_conditional_edges(source_node.name, condition, condition_map)

    def compile(self) -> CompiledStateGraph:
        """Finalizes and returns the compiled graph"""
        return self._graph.compile()
