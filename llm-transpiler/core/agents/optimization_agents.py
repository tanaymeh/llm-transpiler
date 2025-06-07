"""
Optimization agents for project-level transpilation.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from loguru import logger

from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from core.state import ProjectState, State
from core.agents.base import Agent
from core.agents.tracing import with_tracing
from core.agents.utils import sanitize_output


class DirectoryOptimizationAgent(Agent):
    """
    Agent for optimizing a directory of Python files.
    """

    name: str = "directory_optimization"
    optimization_prompt: str

    def plan(self, directory: Path, files: List[Path]) -> list[BaseMessage]:
        """
        Plan the optimization for a directory.

        Args:
            directory: Directory to optimize
            files: List of files in the directory

        Returns:
            List of messages for the LLM
        """
        # Read all files in the directory
        file_contents = {}
        for file_path in files:
            try:
                with open(file_path, "r") as f:
                    file_contents[str(file_path.relative_to(directory))] = f.read()
            except Exception as e:
                logger.error(f"Error reading {file_path}: {str(e)}")
                continue

        # Create context for optimization
        context = {
            "directory": str(directory),
            "files": [str(f.relative_to(directory)) for f in files],
            "file_contents": file_contents,
            "optimization_patterns": [
                "Convert Java-style getters/setters to Python properties",
                "Replace verbose Java collections with Python equivalents",
                "Simplify exception handling",
                "Use more idiomatic Python constructs",
                "Optimize imports and module structure",
            ],
        }

        # Create messages
        messages: list[BaseMessage] = [
            SystemMessage(content=self.optimization_prompt),
            HumanMessage(content=json.dumps(context, indent=2)),
        ]

        return messages

    def execute(
        self,
        directory: Path,
        files: List[Path],
        messages: list[BaseMessage],
        project_root: Path,
    ) -> Dict[str, str]:
        """
        Execute the optimization for a directory.

        Args:
            directory: Directory to optimize
            files: List of files in the directory
            messages: List of messages for the LLM

        Returns:
            Dictionary mapping file paths to optimized content
        """
        logger.info(f"Optimizing directory: {directory}")

        # Get the outputs from the model
        output: AIMessage = self.model.invoke(messages)  # type: ignore

        # Parse the response
        try:
            # The response should be a JSON object mapping file paths to optimized content
            response_text = sanitize_output(output)
            optimizations = json.loads(response_text)

            # Apply optimizations
            results = {}
            for rel_path, new_content in optimizations.items():
                # Convert relative path to absolute path
                file_path = (directory / rel_path).resolve()

                if not file_path.is_relative_to(project_root.resolve()):
                    logger.warning(f"Skipping path outside project: {rel_path}")
                    continue

                if file_path.exists():
                    # Save the optimized content
                    with open(file_path, "w") as f:
                        f.write(new_content)

                    results[str(file_path)] = new_content
                    logger.info(f"Optimized {rel_path}")
                else:
                    logger.warning(f"File not found: {rel_path}")

            return results

        except Exception as e:
            logger.error(f"Error applying optimizations to {directory}: {str(e)}")
            return {}

    def optimize_directory(
        self, directory: Path, files: List[Path], project_root: Path
    ) -> Dict[str, str]:
        """
        Run the optimization for a directory.

        Args:
            directory: Directory to optimize
            files: List of files in the directory

        Returns:
            Dictionary mapping file paths to optimized content
        """
        messages = self.plan(directory, files)
        return self.execute(directory, files, messages, project_root)

    @with_tracing
    def run(self, state: State) -> State:
        """
        Binds the planning and execution stage of an Agent to expose to GraphBuilder.

        This implementation is a wrapper to maintain compatibility with the Agent interface.
        The actual optimization is done by the optimize_directory method.

        Args:
            state: The current state

        Returns:
            The updated state
        """
        # This method is not used directly for optimization agents
        # It's here to maintain compatibility with the Agent interface
        return state


class ProjectOptimizationAgent(Agent):
    """
    Agent for optimizing an entire project.
    """

    name: str = "project_optimization"
    project_optimization_prompt: str

    def plan(self, project_state: ProjectState) -> list[BaseMessage]:
        """
        Plan the optimization for a project.

        Args:
            project_state: Project state

        Returns:
            List of messages for the LLM
        """
        from core.project.structure import get_project_structure

        # Get project structure
        structure = get_project_structure(project_state.target_dir)

        # Create context for optimization
        context = {
            "project_root": str(project_state.target_dir),
            "directory_structure": structure,
            "optimization_focus": [
                "Cross-module consistency",
                "Project-wide patterns",
                "Common utility functions",
                "Shared interfaces and base classes",
            ],
        }

        # Create messages
        messages: list[BaseMessage] = [
            SystemMessage(content=self.project_optimization_prompt),
            HumanMessage(content=json.dumps(context, indent=2)),
        ]

        return messages

    def execute(
        self, project_state: ProjectState, messages: list[BaseMessage]
    ) -> Dict[str, Any]:
        """
        Execute the optimization for a project.

        Args:
            project_state: Project state
            messages: List of messages for the LLM

        Returns:
            Dictionary with optimization results
        """
        logger.info(f"Optimizing project: {project_state.target_dir}")

        # Get the outputs from the model
        output: AIMessage = self.model.invoke(messages)  # type: ignore

        # Parse the response
        try:
            # The response should be a JSON object with file updates and new files
            response_text = sanitize_output(output)
            optimizations = json.loads(response_text)

            results = {
                "updated_files": [],
                "new_files": [],
                "recommendations": optimizations.get("recommendations", []),
            }

            # Apply file updates
            for file_path, new_content in optimizations.get("file_updates", {}).items():
                # Convert relative path to absolute path
                abs_path = project_state.target_dir / file_path

                if abs_path.exists():
                    # Save the optimized content
                    with open(abs_path, "w") as f:
                        f.write(new_content)

                    results["updated_files"].append(str(file_path))
                    logger.info(f"Updated file: {file_path}")
                else:
                    logger.warning(f"File not found: {file_path}")

            # Create new files
            for file_path, content in optimizations.get("new_files", {}).items():
                # Convert relative path to absolute path
                abs_path = project_state.target_dir / file_path

                # Create parent directories
                abs_path.parent.mkdir(parents=True, exist_ok=True)

                # Save the new file
                with open(abs_path, "w") as f:
                    f.write(content)

                results["new_files"].append(str(file_path))
                logger.info(f"Created new file: {file_path}")

            return results

        except Exception as e:
            logger.error(f"Error applying project-wide optimizations: {str(e)}")
            return {
                "updated_files": [],
                "new_files": [],
                "recommendations": [],
                "error": str(e),
            }

    def optimize_project(self, project_state: ProjectState) -> Dict[str, Any]:
        """
        Run the optimization for a project.

        Args:
            project_state: Project state

        Returns:
            Dictionary with optimization results
        """
        messages = self.plan(project_state)
        return self.execute(project_state, messages)

    @with_tracing
    def run(self, state: State) -> State:
        """
        Binds the planning and execution stage of an Agent to expose to GraphBuilder.

        This implementation is a wrapper to maintain compatibility with the Agent interface.
        The actual optimization is done by the optimize_project method.

        Args:
            state: The current state

        Returns:
            The updated state
        """
        # This method is not used directly for optimization agents
        # It's here to maintain compatibility with the Agent interface
        return state


class ProjectOptimizer:
    """
    Orchestrates the optimization of a project.
    """

    def __init__(
        self, project_state: ProjectState, model_name: str, api_key: str, base_url: str
    ):
        """
        Initialize the project optimizer.

        Args:
            project_state: Project state
            model_name: Model name
            api_key: OpenAI API key
            base_url: OpenAI API base URL
        """
        self.project_state = project_state

        # Initialize LLM client
        model = ChatOpenAI(
            model=model_name,
            temperature=0.2,
            api_key=SecretStr(api_key),
            base_url=base_url,
        )

        # Load optimization prompts
        self.directory_optimization_prompt = """You are a Python optimization expert tasked with improving transpiled Java-to-Python code.
Your job is to make the code more idiomatic and Pythonic while preserving its functionality.

You will receive a JSON object containing:
1. The directory being optimized
2. A list of Python files in that directory
3. The content of each file
4. A list of optimization patterns to apply
All paths are relative to the directory being optimized.

For each file, apply these optimizations:
- Convert Java-style getters/setters to Python properties
- Replace verbose Java collections with Python equivalents (e.g., ArrayList → list)
- Simplify exception handling to use more Pythonic patterns
- Use more idiomatic Python constructs (list comprehensions, context managers, etc.)
- Optimize imports and module structure

IMPORTANT RULES:
1. Preserve all public API signatures and behavior
2. Maintain compatibility with other modules in the project
3. Ensure the code remains functionally identical
4. Focus on readability and Pythonic style

Return a JSON object where:
- Keys are the relative file paths (relative to the directory being optimized)
- Values are the optimized file contents
"""

        self.project_optimization_prompt = """You are a Python architecture expert tasked with project-wide optimization of transpiled Java-to-Python code.
Your job is to identify and implement cross-module improvements while preserving functionality.

You will receive a JSON object containing:
1. The project root directory
2. The directory structure with all Python files
3. A list of optimization focus areas

Analyze the project structure and implement these optimizations:
- Ensure consistent coding style across modules
- Identify common patterns that could be extracted to utility functions
- Optimize cross-module dependencies and imports
- Apply consistent design patterns throughout the project
- Improve project organization where appropriate

IMPORTANT RULES:
1. Preserve all public API signatures and behavior
2. Maintain backward compatibility
3. Ensure the code remains functionally identical
4. Focus on maintainability and consistency

Return a JSON object with:
1. "file_updates": A dictionary mapping file paths to their optimized content
2. "new_files": A dictionary of new utility files to create
3. "recommendations": A list of additional manual improvements that could be made
"""

        # Initialize agents
        self.directory_agent = DirectoryOptimizationAgent(
            model=model,
            system_prompt=self.directory_optimization_prompt,
            optimization_prompt=self.directory_optimization_prompt,
        )

        self.project_agent = ProjectOptimizationAgent(
            model=model,
            system_prompt=self.project_optimization_prompt,
            project_optimization_prompt=self.project_optimization_prompt,
        )

    def optimize(self) -> Dict[str, Any]:
        """
        Optimize the project.

        Returns:
            Dictionary with optimization results
        """
        logger.info(
            f"Starting project optimization for {self.project_state.target_dir}"
        )

        # Get all directories in the target project
        all_dirs = set()
        py_files_by_dir = {}

        for py_file in self.project_state.target_dir.glob("**/*.py"):
            # Skip test files
            if "_test.py" in py_file.name:
                continue

            dir_path = py_file.parent
            all_dirs.add(dir_path)

            if dir_path not in py_files_by_dir:
                py_files_by_dir[dir_path] = []

            py_files_by_dir[dir_path].append(py_file)

        # Sort directories by depth (deepest first)
        sorted_dirs = sorted(all_dirs, key=lambda d: len(d.parts), reverse=True)

        # Process directories bottom-up
        directory_results = {}
        for directory in sorted_dirs:
            if directory in py_files_by_dir and py_files_by_dir[directory]:
                result = self.directory_agent.optimize_directory(
                    directory,
                    py_files_by_dir[directory],
                    self.project_state.target_dir,
                )
                directory_results[str(directory)] = result

        # Final project-wide optimization
        project_results = self.project_agent.optimize_project(self.project_state)

        # Combine results
        results = {
            "directory_optimizations": directory_results,
            "project_optimization": project_results,
        }

        logger.info("Project optimization complete")
        return results
