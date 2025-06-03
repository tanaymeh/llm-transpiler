"""
Project structure cloning functionality for project-level transpilation.
"""

from pathlib import Path
from typing import Dict, List
from loguru import logger


def clone_project_structure(source_dir: Path, target_dir: Path) -> Dict[Path, Path]:
    """
    Clone the project structure from source to target directory.

    Args:
        source_dir: Source project directory
        target_dir: Target project directory

    Returns:
        Dictionary mapping source files to target files
    """
    # Create target directory if it doesn't exist
    target_dir.mkdir(parents=True, exist_ok=True)

    # Map to store source to target file mappings
    file_mapping = {}

    # Walk through source directory
    for source_file in source_dir.glob("**/*.java"):
        # Get relative path
        rel_path = source_file.relative_to(source_dir)

        # Create target path with .py extension
        target_path = target_dir / rel_path.with_suffix(".py")

        # Create parent directories
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Create empty file
        target_path.touch()

        # Add to mapping
        file_mapping[source_file] = target_path

        logger.debug(f"Mapped {source_file} -> {target_path}")

    logger.info(f"Cloned project structure: {len(file_mapping)} files mapped")
    return file_mapping


def get_project_structure(directory: Path) -> Dict:
    """
    Get a dictionary representation of the project directory structure.

    Args:
        directory: Project directory

    Returns:
        Dictionary representing the directory structure
    """
    structure = {}

    for file_path in directory.glob("**/*"):
        if file_path.is_dir():
            continue

        rel_path = file_path.relative_to(directory)
        parts = rel_path.parts

        current = structure
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                # This is a file
                current.setdefault("files", []).append(part)
            else:
                # This is a directory
                current.setdefault("dirs", {}).setdefault(part, {})
                current = current["dirs"][part]

    return structure
