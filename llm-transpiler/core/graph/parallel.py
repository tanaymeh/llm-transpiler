"""
Parallel execution management for project-level transpilation.
"""

import time
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, Set, Optional, Callable
from loguru import logger

from core.state import ProjectState, FileState, StateError


class ParallelExecutionManager:
    """Manages parallel execution of file transpilation agents."""

    def __init__(
        self,
        project_state: ProjectState,
        file_processor: Callable[[Path, Path, str, int], bool],
        on_file_complete: Optional[Callable[[Path, bool], None]] = None,
        on_all_complete: Optional[Callable[[], None]] = None,
    ):
        """
        Initialize the parallel execution manager.

        Args:
            project_state: The project state
            file_processor: Function that processes a single file (source_file, target_file, model_name, max_retries) -> success
            on_file_complete: Optional callback when a file is completed
            on_all_complete: Optional callback when all files are completed
        """
        self.project_state = project_state
        self.file_processor = file_processor
        self.on_file_complete = on_file_complete
        self.on_all_complete = on_all_complete
        self.executor = ThreadPoolExecutor(max_workers=project_state.concurrency)
        self.completed_files: Set[Path] = set()
        self.failed_files: Set[Path] = set()
        self.in_progress: Set[Path] = set()
        self.lock = threading.Lock()

    def get_next_batch(self) -> List[Path]:
        """Get the next batch of files to transpile based on dependencies."""
        with self.lock:
            available = []

            for file_path, file_state in self.project_state.file_states.items():
                # Skip files that are completed, failed, or in progress
                if (
                    file_path in self.completed_files
                    or file_path in self.failed_files
                    or file_path in self.in_progress
                ):
                    continue

                # Check if all dependencies are completed
                deps = self.project_state.dependencies.get(file_path, [])
                if all(dep in self.completed_files for dep in deps):
                    available.append(file_path)

                    # Limit batch size to available concurrency
                    if len(available) >= self.project_state.concurrency - len(
                        self.in_progress
                    ):
                        break

            # Mark selected files as in progress
            self.in_progress.update(available)

            return available

    def process_file(self, file_path: Path) -> None:
        """Process a single file."""
        try:
            file_state = self.project_state.file_states[file_path]
            file_state.transpilation_status = "in_progress"

            # Get target file path
            target_file = file_state.target_path
            if target_file is None:
                logger.error(f"No target path for {file_path}")
                raise ValueError(f"No target path for {file_path}")

            # Process the file
            success = self.file_processor(
                file_path,
                target_file,
                self.project_state.model_name,
                self.project_state.max_retries,
            )

            with self.lock:
                self.in_progress.remove(file_path)

                if success:
                    self.completed_files.add(file_path)
                    file_state.transpilation_status = "completed"
                    self.progress_queue.put(1)
                else:
                    self.failed_files.add(file_path)
                    file_state.transpilation_status = "failed"
                    file_state.retry_count += 1

                    # Add to manual review if max retries reached
                    if file_state.retry_count >= self.project_state.max_retries:
                        self.project_state.manual_review_files.append(
                            {
                                "file": str(file_path),
                                "errors": file_state.error_reports,
                                "dependencies": [
                                    str(dep)
                                    for dep in self.project_state.dependencies.get(
                                        file_path, []
                                    )
                                ],
                            }
                        )
                        logger.warning(
                            f"File {file_path} failed after {file_state.retry_count} attempts, added to manual review"
                        )

            # Call the completion callback if provided
            if self.on_file_complete:
                self.on_file_complete(file_path, success)

        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")
            with self.lock:
                if file_path in self.in_progress:
                    self.in_progress.remove(file_path)
                self.failed_files.add(file_path)

                file_state = self.project_state.file_states[file_path]
                file_state.transpilation_status = "failed"
                file_state.error_reports.append(
                    {"error": str(e), "traceback": traceback.format_exc()}
                )

                # Add to manual review
                self.project_state.manual_review_files.append(
                    {
                        "file": str(file_path),
                        "errors": file_state.error_reports,
                        "dependencies": [
                            str(dep)
                            for dep in self.project_state.dependencies.get(
                                file_path, []
                            )
                        ],
                    }
                )

    def run(self) -> None:
        """Run the parallel transpilation process until all files are processed."""
        from tqdm import tqdm
        import queue
        from threading import Event

        total_files = len(self.project_state.file_states)
        self.progress_queue = queue.Queue()
        done_event = Event()

        # Progress bar thread
        def update_progress():
            with tqdm(
                total=total_files,
                desc="Transpiling files",
                unit="file",
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]",
            ) as pbar:
                while not done_event.is_set() or not self.progress_queue.empty():
                    try:
                        amount = self.progress_queue.get(timeout=0.1)
                        pbar.update(amount)
                    except queue.Empty:
                        continue

        # Start progress thread
        import threading

        progress_thread = threading.Thread(target=update_progress)
        progress_thread.start()

        try:
            while len(self.completed_files) + len(self.failed_files) < len(
                self.project_state.file_states
            ):
                batch = self.get_next_batch()

                if not batch:
                    # If no files are available but we're not done, wait for in-progress tasks
                    if self.in_progress:
                        # Removed verbose debug logging
                        time.sleep(0.5)
                        continue
                    else:
                        # If nothing is in progress and nothing is available, we might have a dependency cycle
                        logger.warning("Possible dependency cycle detected")

                        # Find files that haven't been processed yet
                        remaining = []
                        for file_path in self.project_state.file_states:
                            if (
                                file_path not in self.completed_files
                                and file_path not in self.failed_files
                                and file_path not in self.in_progress
                            ):
                                remaining.append(file_path)

                        if not remaining:
                            # This shouldn't happen, but just in case
                            break

                        # Process one file ignoring dependencies
                        # Removed verbose status logging
                        with self.lock:
                            self.in_progress.add(remaining[0])
                        self.executor.submit(self.process_file, remaining[0])
                        continue

                logger.info(f"Submitting batch of {len(batch)} files for processing")

                # Submit batch to executor
                futures = [
                    self.executor.submit(self.process_file, file_path)
                    for file_path in batch
                ]

            logger.info("All files processed")

            # Call the completion callback if provided
            if self.on_all_complete:
                self.on_all_complete()

        finally:
            self.executor.shutdown()

        # Log final statistics
        total = len(self.project_state.file_states)
        completed = len(self.completed_files)
        failed = len(self.failed_files)

        logger.info(
            f"Transpilation complete: {completed}/{total} files successful, {failed} failed"
        )

        if self.project_state.manual_review_files:
            logger.warning(
                f"{len(self.project_state.manual_review_files)} files need manual review"
            )


class SingleFileProcessor:
    """Adapter for processing a single file using the existing transpilation workflow."""

    @staticmethod
    def process_file(
        source_file: Path, target_file: Path, model_name: str, max_retries: int
    ) -> bool:
        """
        Process a single file using the existing transpilation workflow.

        Args:
            source_file: Source file path
            target_file: Target file path
            model_name: Model name
            max_retries: Maximum number of retries

        Returns:
            True if successful, False otherwise
        """
        from core.agents import (
            SummaryAgent,
            PlanningAgent,
            TranspileAgent,
            python_format,
            save_to_disk,
        )
        from core.graph.builder import GraphBuilder
        from core.state import State, StateError
        from langgraph.graph import END
        from langchain_openai import ChatOpenAI
        from prompts import Prompts
        import os
        from dotenv import load_dotenv
        from pydantic import SecretStr

        _ = load_dotenv()

        try:
            # Load environment variables fresh in case we're in a subprocess
            load_dotenv()

            # Get API key with fallback
            api_key = os.getenv("OPEN_API_KEY")
            if not api_key:
                raise ValueError(
                    "OPEN_API_KEY or OPENAI_API_KEY environment variable required. "
                    "Please set one of these in your .env file or environment."
                )

            # Initialize LLM client
            model = ChatOpenAI(
                model=model_name,
                temperature=0.2,
                api_key=SecretStr(api_key),
                base_url=os.getenv("OPEN_BASE_URL", "https://api.openai.com/v1"),
            )

            # Load prompts
            prompts = Prompts()

            # Read source code
            with open(source_file, "r") as sf:
                source_code = sf.read()

            # Create initial State
            state = State(
                code="",
                original_code=source_code,
                scratchpad="",
                last_error=StateError(status=0, message=""),
                current_iterations=0,
            )

            # Add project context to system prompt
            project_context = """
            IMPORTANT: This file is part of a larger project being transpiled from Java to Python.
            Other files in the project will be transpiled separately, maintaining the same class and function names.
            Ensure your transpiled code:
            1. Keeps all class, method, and function names identical to the Java version
            2. Maintains the same public API and signatures
            3. Uses relative imports for project dependencies
            4. Is functionally identical to the original Java code
            """

            # Instantiate agents with prompts
            summary_agent = SummaryAgent(
                model=model,
                system_prompt=prompts.SUMMARY_AGENT_SYSTEM_PROMPT,
                summary_user_prompt=prompts.SUMMARY_AGENT_USER_PROMPT,
            )

            # Add project context to planning agent prompt
            planning_prompt = (
                prompts.PLANNING_AGENT_SYSTEM_PROMPT + "\n\n" + project_context
            )

            planning_agent = PlanningAgent(
                model=model,
                system_prompt=planning_prompt,
                planning_user_prompt=prompts.PLANNING_AGENT_USER_PROMPT,
            )

            transpile_agent = TranspileAgent(
                model=model,
                system_prompt=prompts.TRANSPILE_AGENT_SYSTEM_PROMPT,
                transpile_user_prompt=prompts.TRANSPILE_AGENT_USER_PROMPT,
                error_prompts={
                    1: prompts.TRANSPILE_AGENT_COMPILE_ERROR_PROMPT,
                    2: prompts.TRANSPILE_AGENT_OUTPUT_MATCH_ERROR_PROMPT,
                },
            )

            # Build the graph
            gb = GraphBuilder()
            gb.add_node(summary_agent)
            gb.add_node(planning_agent)
            gb.add_node(transpile_agent)

            # Define workflow edges
            gb.set_entry_point(summary_agent)
            gb.add_edge(summary_agent, planning_agent)
            gb.add_edge(planning_agent, transpile_agent)

            # Add conditional edge for retries
            gb.add_conditional_edge(
                transpile_agent,
                lambda s: (
                    "continue"
                    if s.last_error.status != 0 and s.current_iterations < max_retries
                    else "terminate"
                ),
                {"continue": transpile_agent.name, "terminate": END},
            )

            # Compile and run the state graph
            graph = gb.compile()
            final_state = graph.invoke(state)

            # Post-processing with tools
            final_state["code"] = python_format(final_state["code"])
            save_to_disk(final_state["code"], str(target_file))

            return final_state["last_error"].status == 0

        except Exception as e:
            logger.error(f"Error in SingleFileProcessor for {source_file}: {str(e)}")
            return False
