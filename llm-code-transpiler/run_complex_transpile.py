#!/usr/bin/env python3
"""
CLI script to run the complex transpile workflow using the new Agent-based architecture.
"""
import os
import argparse
import json

from langgraph.graph import END
from langchain_openai import ChatOpenAI

from core import (
    State,
    StateError,
    GraphBuilder,
    SummaryAgent,
    PlanningAgent,
    TranspileAgent,
    python_format,
    save_to_disk,
)
from prompts import Prompts

from dotenv import load_dotenv


def compile_condition(state: State, max_iter: int):
    """Decides whether to continue transpilation on compile error or terminate."""
    if state.last_error.status != 0 and state.current_iterations < max_iter:
        return "continue"
    return "terminate"


def main():
    _ = load_dotenv()
    parser = argparse.ArgumentParser(description="Run complex transpile workflow")
    parser.add_argument("--model-name", required=True, help="LLM model name")
    parser.add_argument("--source", required=True, help="Path to source code file")
    parser.add_argument("--target", required=True, help="Path to target output file")
    parser.add_argument(
        "--max-iter",
        type=int,
        default=3,
        help="Maximum transpilation iterations on error",
    )
    args = parser.parse_args()

    # Load prompt templates
    with open(args.prompts, "r") as pf:
        prompts = json.load(pf)

    # Initialize LLM client
    model = ChatOpenAI(
        model=args.model_name,
        temperature=0.2,
        api_key=os.environ["OPEN_API_KEY"],  # type: ignore
        base_url=os.environ["OPEN_BASE_URL"],
    )

    # Read source code
    with open(args.source, "r") as sf:
        source_code = sf.read()

    # Create initial State
    state = State(
        code="",
        original_code=source_code,
        scratchpad="",
        last_error=StateError(status=0, message=""),
        current_iterations=0,
    )

    # Instantiate agents with prompts
    summary_agent = SummaryAgent(
        model=model,
        system_prompt=Prompts.SUMMARY_AGENT_SYSTEM_PROMPT,
        summary_user_prompt=Prompts.SUMMARY_AGENT_USER_PROMPT,
    )
    planning_agent = PlanningAgent(
        model=model,
        system_prompt=Prompts.PLANNING_AGENT_SYSTEM_PROMPT,
        planning_user_prompt=Prompts.PLANNING_AGENT_USER_PROMPT,
    )
    # search_agent = SearchAgent(
    #     model=model,
    #     system_prompt=prompts["questions"],
    # )
    transpile_agent = TranspileAgent(
        model=model,
        system_prompt=Prompts.TRANSPILE_AGENT_SYSTEM_PROMPT,
        transpile_user_prompt=Prompts.TRANSPILE_AGENT_USER_PROMPT,
        error_prompts={
            1: Prompts.TRANSPILE_AGENT_COMPILE_ERROR_PROMPT,
            2: Prompts.TRANSPILE_AGENT_OUTPUT_MATCH_ERROR_PROMPT,
        },
    )

    # Build the graph
    gb = GraphBuilder()
    gb.add_node(summary_agent)
    gb.add_node(planning_agent)
    # gb.add_node(search_agent)
    gb.add_node(transpile_agent)

    # Define workflow edges
    gb.set_entry_point(summary_agent)
    gb.add_edge(summary_agent, planning_agent)
    gb.add_edge(planning_agent, transpile_agent)
    # gb.add_edge(search_agent, transpile_agent)
    gb.add_conditional_edge(
        transpile_agent,
        lambda s: compile_condition(s, args.max_iter),
        {"continue": transpile_agent.name, "terminate": END},
    )

    # Compile and run the state graph
    graph = gb.compile()
    final_state = graph.invoke(state)

    # Post-processing with tools
    final_state["code"] = python_format(final_state["code"])
    save_to_disk(final_state["code"], args.target)


if __name__ == "__main__":
    main()
