"""
Test management functionality for project-level transpilation.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage


def identify_test_files(source_dir: Path) -> List[Path]:
    """
    Identify test files in the source project.

    Args:
        source_dir: Source project directory

    Returns:
        List of test file paths
    """
    test_files = []

    # Common patterns for test files
    test_patterns = [
        r".*Test\.java$",
        r".*Tests\.java$",
        r"Test.*\.java$",
        r".*IT\.java$",  # Integration tests
        r".*Spec\.java$",  # Specification tests
    ]

    # Compile patterns
    compiled_patterns = [re.compile(pattern) for pattern in test_patterns]

    # Find files matching patterns
    for java_file in source_dir.glob("**/*.java"):
        file_name = java_file.name

        # Check if file name matches any test pattern
        if any(pattern.match(file_name) for pattern in compiled_patterns):
            test_files.append(java_file)
            continue

        # Check file content for JUnit annotations
        try:
            with open(java_file, "r") as f:
                content = f.read()

            # Look for common test annotations
            if re.search(r"@Test\b", content) or re.search(
                r"extends\s+TestCase", content
            ):
                test_files.append(java_file)
        except UnicodeDecodeError:
            logger.warning(f"Could not read {java_file} - skipping")

    logger.info(f"Found {len(test_files)} test files in project")
    return test_files


def clone_test_files(
    test_files: List[Path],
    source_dir: Path,
    target_dir: Path,
    model: Optional[ChatOpenAI] = None,
) -> Dict[Path, Path]:
    """
    Clone test files from Java to Python.

    Args:
        test_files: List of Java test files
        source_dir: Source project directory
        target_dir: Target project directory
        model: Optional LLM model for test conversion

    Returns:
        Dictionary mapping source test files to target test files
    """
    test_mapping = {}

    for java_test in test_files:
        # Get relative path
        rel_path = java_test.relative_to(source_dir)

        # Create target path with _test.py suffix
        # Convert CamelCase to snake_case for the file name (assuming names are in camel case but then again, i don't trust java devs lol)
        stem = rel_path.stem
        snake_case = "".join(
            ["_" + c.lower() if c.isupper() else c for c in stem]
        ).lstrip("_")
        target_path = target_dir / rel_path.parent / f"{snake_case}_test.py"

        # Create parent directories
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # If model is provided, use it to convert the test
        if model:
            try:
                with open(java_test, "r") as f:
                    java_content = f.read()

                # Convert Java test to Python test
                python_test = convert_test(java_content, model)

                # Write converted test
                with open(target_path, "w") as f:
                    f.write(python_test)

                logger.info(f"Converted test {java_test} -> {target_path}")
            except Exception as e:
                logger.error(f"Error converting test {java_test}: {str(e)}")
                # Create empty file as fallback
                target_path.touch()
        else:
            # Just create empty file
            target_path.touch()
            logger.info(f"Created empty test file {target_path}")

        test_mapping[java_test] = target_path

    return test_mapping


def convert_test(java_test: str, model: ChatOpenAI) -> str:
    """
    Convert a Java test to a Python test using LLM.

    Args:
        java_test: Java test content
        model: LLM model for test conversion

    Returns:
        Converted Python test content
    """
    system_prompt = """You are a test conversion expert. Your task is to convert Java tests to Python pytest tests.
Follow these guidelines:
1. Convert JUnit assertions to pytest assertions
2. Replace assertEquals with assert a == b
3. Replace assertTrue with assert condition
4. Replace assertFalse with assert not condition
5. Replace assertNull with assert obj is None
6. Replace assertNotNull with assert obj is not None
7. Add appropriate imports (pytest, etc.)
8. Convert setup/teardown methods to pytest fixtures
9. Maintain the same test logic and coverage
10. Use Pythonic naming conventions (snake_case for methods)
11. Return ONLY the Python code without any explanation or markdown formatting

The output should be a valid Python file that can be run with pytest.
"""

    user_prompt = f"""Convert the following Java test to a Python pytest test:

```java
{java_test}
```

Remember to follow Pythonic conventions and pytest best practices.
"""

    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]

    response = model.invoke(messages)

    # Extract code from response
    content = str(response.content)

    # Remove markdown code blocks if present
    if "```python" in content and "```" in content:
        match = re.search(r"```python\n(.*?)```", content, re.DOTALL)
        if match:
            return match.group(1).strip()

    # Remove any explanations before or after the code
    lines = content.split("\n")
    code_lines = []
    in_code = False

    for line in lines:
        if (
            line.strip().startswith("import ")
            or line.strip().startswith("def ")
            or line.strip().startswith("class ")
        ):
            in_code = True

        if in_code:
            code_lines.append(line)

    if code_lines:
        return "\n".join(code_lines)

    # If we couldn't extract code properly, return the whole response
    return content


def generate_tests(
    source_files: List[Path], target_files: List[Path], model: ChatOpenAI
) -> Dict[Path, str]:
    """
    Generate Python tests for transpiled files that don't have tests.

    Args:
        source_files: List of source Java files
        target_files: List of target Python files
        model: LLM model for test generation

    Returns:
        Dictionary mapping target test files to generated test content
    """
    generated_tests = {}

    for source_file, target_file in zip(source_files, target_files):
        # Skip if source file is a test
        if "test" in source_file.stem.lower():
            continue

        # Create test file path
        test_path = target_file.parent / f"{target_file.stem}_test.py"

        try:
            # Read source and target files
            with open(source_file, "r") as f:
                java_content = f.read()

            with open(target_file, "r") as f:
                python_content = f.read()

            # Generate test
            test_content = generate_test_for_file(java_content, python_content, model)

            # Create parent directories
            test_path.parent.mkdir(parents=True, exist_ok=True)

            # Write test file
            with open(test_path, "w") as f:
                f.write(test_content)

            generated_tests[test_path] = test_content
            logger.info(f"Generated test for {target_file} -> {test_path}")

        except Exception as e:
            logger.error(f"Error generating test for {target_file}: {str(e)}")

    return generated_tests


def generate_test_for_file(
    java_content: str, python_content: str, model: ChatOpenAI
) -> str:
    """
    Generate a Python test for a transpiled file.

    Args:
        java_content: Original Java file content
        python_content: Transpiled Python file content
        model: LLM model for test generation

    Returns:
        Generated Python test content
    """
    system_prompt = """You are a test generation expert. Your task is to generate pytest tests for a Python file that was transpiled from Java.
Follow these guidelines:
1. Create comprehensive tests that cover the main functionality
2. Use pytest fixtures where appropriate
3. Include tests for edge cases and error conditions
4. Use descriptive test names that explain what is being tested
5. Follow pytest best practices
6. Return ONLY the Python test code without any explanation or markdown formatting

The output should be a valid Python file that can be run with pytest.
"""

    user_prompt = f"""Generate pytest tests for the following Python file that was transpiled from Java.

Original Java code:
```java
{java_content}
```

Transpiled Python code:
```python
{python_content}
```

Create comprehensive tests that verify the functionality works as expected.
"""

    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]

    response = model.invoke(messages)

    # Extract code from response
    content = str(response.content)

    # Remove markdown code blocks if present
    if "```python" in content and "```" in content:
        match = re.search(r"```python\n(.*?)```", content, re.DOTALL)
        if match:
            return match.group(1).strip()

    # Remove any explanations before or after the code
    lines = content.split("\n")
    code_lines = []
    in_code = False

    for line in lines:
        if (
            line.strip().startswith("import ")
            or line.strip().startswith("def ")
            or line.strip().startswith("class ")
        ):
            in_code = True

        if in_code:
            code_lines.append(line)

    if code_lines:
        return "\n".join(code_lines)

    # If we couldn't extract code properly, return the whole response
    return content
