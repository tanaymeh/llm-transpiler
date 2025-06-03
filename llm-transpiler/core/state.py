from pydantic import BaseModel, Field
from pathlib import Path
from typing import Dict, List, Optional, Any


class StateError(BaseModel):
    """
    Error for a transpilation state

    Error codes:
        0: No error
        1: Compilation error
        2: Runtime error (dummy test)
        3: Outputs not matched error (real test)
    """

    status: int = Field(0, ge=0, le=3)
    message: str


class State(BaseModel):
    """Transpilation workflow state"""

    code: str
    original_code: str
    scratchpad: str
    last_error: StateError
    current_iterations: int


class FileState(State):
    """Extended state for file-level transpilation"""

    relative_path: Path  # Path relative to project root
    target_path: Optional[Path] = None  # Path to the target file
    dependencies: List[Path] = Field(default_factory=list)  # Files this file depends on
    transpilation_status: str = (
        "pending"  # e.g., "pending", "in_progress", "completed", "failed"
    )
    optimization_status: str = "pending"  # e.g., "pending", "completed"
    retry_count: int = 0  # Number of transpilation attempts
    error_reports: List[Dict[str, Any]] = Field(
        default_factory=list
    )  # Detailed error reports for failed attempts


class ProjectState(BaseModel):
    """Project-level transpilation state"""

    source_dir: Path
    target_dir: Path
    file_states: Dict[Path, FileState]  # Maps source paths to individual file states
    dependencies: Dict[Path, List[Path]] = Field(
        default_factory=dict
    )  # File dependency graph
    optimization_context: Dict[str, Any] = Field(
        default_factory=dict
    )  # Shared context for optimization pass
    current_phase: str = "init"  # e.g., "structure_clone", "transpile", "optimize"
    max_retries: int = 2  # Number of retries for failed transpilations
    concurrency: int = 3  # Number of parallel transpilation agents
    manual_review_files: List[Dict[str, Any]] = Field(
        default_factory=list
    )  # Files that failed transpilation with error reports
    model_name: str  # LLM model name to use for transpilation
