import os
import re
import ast
import subprocess

from typing import Any, List

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage


def python_compile(code: str, error: dict):
    """Compiles Python code and catches any compile-time errors"""
    try:
        # Try to parse the code string into an AST
        ast.parse(code)
        error["status"] = 0
        error["message"] = ""
        return error

    except SyntaxError as e:
        error["status"] = 1
        error["message"] = (
            f"SyntaxError: {str(e)}\n"
            f"Line {e.lineno}, Column {e.offset}\n"
            f"{e.text}\n"
            f"{' ' * (e.offset - 1)}^"
        )
        return error

    except Exception as e:
        error["status"] = 1
        error["message"] = f"Compilation Error: {str(e)}"
        return error


def java_compile(file: str):
    """Compiles Java code"""
    try:
        output = subprocess.check_call(
            ["bash", "javac", file], stderr=subprocess.STDOUT
        )
    except subprocess.CalledProcessError as e:
        error_str = e.output.decoce("utf-8")
        return (1, error_str)

    return (0, "")


def sanitize_output(code: str):
    """Sanitizes the output returned by the model"""
    markdown_pattern = r"^\s*```python\s*([\s\S]*)\s*```\s*$"
    markdown_match = re.match(markdown_pattern, code, re.MULTILINE)

    if markdown_match:
        return markdown_match.group(1).strip()

    code_blocks = re.findall(r"```python\s*([\s\S]*?)\s*```", code, re.MULTILINE)

    if code_blocks:
        return "\n\n".join(block.strip() for block in code_blocks)

    lines = code.split("\n")
    code_lines = []
    for line in lines:
        stripped = line.strip()
        if (not stripped.startswith(("#", "//", "/*", "*", '"""', "'''"))) and stripped:
            code_lines.append(line)

    return "\n".join(code_lines)


def generate_questions(model: Any, state: Any, template: str) -> List:
    """Generates questions about a code file given a model, state and template"""
    messages = [
        SystemMessage(content=template.format(state["scratchpad"])),
        HumanMessage(content=state["original_code"]),
    ]

    # Generate questions
    questions = model(messages)
    questions = questions.content.split(".")

    return questions
