"""
Dependency analysis functionality for project-level transpilation.
"""

import re
from pathlib import Path
from typing import Dict, List, Set
from loguru import logger


def analyze_dependencies(source_dir: Path) -> Dict[Path, List[Path]]:
    """
    Analyze dependencies between Java files in the project.

    Args:
        source_dir: Source project directory

    Returns:
        Dictionary mapping files to their dependencies
    """
    dependencies = {}

    # Map of class names to file paths
    class_to_file = {}
    package_to_dir = {}

    logger.info("Analyzing Java class definitions")

    # First pass: identify all class definitions and package structures
    for java_file in source_dir.glob("**/*.java"):
        with open(java_file, "r") as f:
            try:
                content = f.read()
            except UnicodeDecodeError:
                logger.warning(f"Could not read {java_file} - skipping")
                continue

        # Extract package name
        package_match = re.search(r"package\s+([\w.]+);", content)
        package_name = package_match.group(1) if package_match else ""

        # Map package to directory
        if package_name:
            package_to_dir[package_name] = java_file.parent

        # Simple regex to find class/interface names
        class_matches = re.findall(r"(class|interface|enum)\s+(\w+)", content)
        for _, class_name in class_matches:
            # Store with package prefix for fully qualified name
            if package_name:
                fully_qualified = f"{package_name}.{class_name}"
                class_to_file[fully_qualified] = java_file

            # Also store just the class name for simple references
            class_to_file[class_name] = java_file

    logger.info(f"Found {len(class_to_file)} classes in project")

    # Second pass: identify imports and dependencies
    logger.info("Analyzing Java imports and dependencies")

    for java_file in source_dir.glob("**/*.java"):
        with open(java_file, "r") as f:
            try:
                content = f.read()
            except UnicodeDecodeError:
                continue

        # Find import statements
        import_matches = re.findall(r"import\s+([\w.]+)(?:\.\*)?;", content)

        file_deps = set()
        for import_path in import_matches:
            # Check if this is a direct class import
            if import_path in class_to_file:
                file_deps.add(class_to_file[import_path])
                continue

            # Check if this is a wildcard import (package.*)
            for class_name, file_path in class_to_file.items():
                if class_name.startswith(f"{import_path}."):
                    file_deps.add(file_path)

        # Also check for direct class references in the code
        # This is a simplistic approach and might miss some dependencies
        for class_name, file_path in class_to_file.items():
            # Skip if it's just a simple name that might have many matches
            if "." not in class_name and len(class_name) < 4:
                continue

            # Look for the class name in the code
            if re.search(r"\b" + re.escape(class_name) + r"\b", content):
                file_deps.add(file_path)

        # Remove self-dependency
        if java_file in file_deps:
            file_deps.remove(java_file)

        dependencies[java_file] = list(file_deps)

    logger.info("Dependency analysis complete")
    return dependencies


def build_dependency_graph(
    dependencies: Dict[Path, List[Path]],
) -> Dict[Path, Set[Path]]:
    """
    Build a complete dependency graph including transitive dependencies.

    Args:
        dependencies: Dictionary mapping files to their direct dependencies

    Returns:
        Dictionary mapping files to all their dependencies (direct and transitive)
    """
    graph = {file: set(deps) for file, deps in dependencies.items()}

    # Add files that have no dependencies but are dependencies of others
    all_deps = set()
    for deps in dependencies.values():
        all_deps.update(deps)

    for dep in all_deps:
        if dep not in graph:
            graph[dep] = set()

    # Floyd-Warshall algorithm to find transitive dependencies
    for k in graph:
        for i in graph:
            if k in graph[i]:
                for j in graph[k]:
                    graph[i].add(j)

    return graph


def get_transpilation_order(dependencies: Dict[Path, List[Path]]) -> List[Path]:
    """
    Determine an optimal order for transpiling files based on dependencies.

    Args:
        dependencies: Dictionary mapping files to their dependencies

    Returns:
        List of files in an order suitable for transpilation
    """
    # Build a complete dependency graph
    graph = build_dependency_graph(dependencies)

    # Count incoming edges for each node
    incoming_edges = {node: 0 for node in graph}
    for node, deps in graph.items():
        for dep in deps:
            incoming_edges[dep] = incoming_edges.get(dep, 0) + 1

    # Start with nodes that have no dependencies
    queue = [node for node, count in incoming_edges.items() if count == 0]
    result = []

    # Process nodes in topological order
    while queue:
        node = queue.pop(0)
        result.append(node)

        # Update incoming edges for dependent nodes
        for dependent in [n for n, deps in graph.items() if node in deps]:
            incoming_edges[dependent] -= 1
            if incoming_edges[dependent] == 0:
                queue.append(dependent)

    # Check for cycles
    if len(result) != len(graph):
        logger.warning("Dependency cycle detected in project")
        # Add remaining nodes in any order
        for node in graph:
            if node not in result:
                result.append(node)

    return result
