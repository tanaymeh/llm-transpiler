from langgraph.graph import StateGraph
from ..state import State
from ..nodes import Node


class GraphBuilder:
    """Factor for creating and configuring the transpilation graph"""

    def __init__(self):
        self._graph = StateGraph(state_schema=State)
        self._is_compiled = False

    def add_node(self, name: str, node: Node) -> None:
        """Adds a node to the graph"""
        self._graph.add_node(node.name, node.func)

    def set_entry_point(self, node: Node) -> None:
        """Sets a graph entry point"""
        self._graph.set_entry_point(node.name)

    def _validate_graph(self) -> None:
        """Placeholder for graph validation function"""
        pass

    def add_conditional_edge(
        self, source_node: Node, condition: callable, condition_map: dict
    ) -> None:
        """Adds a conditional edge to the graph between a source and single or multiple target nodes"""
        self._graph.add_conditional_edges(source_node, condition, condition_map)

    def compile(self) -> StateGraph:
        """Finalizes and returns the compiled graph"""
        if not self._is_compiled:
            self._validate_graph()
