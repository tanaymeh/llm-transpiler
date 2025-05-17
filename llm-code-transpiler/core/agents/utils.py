import os
import re
import black
from loguru import logger
from core.state import State, StateError

import textwrap
from typing import cast
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI


def python_compile(code: str, filename: str = "<string>") -> StateError:
    """
    Try to compile a Python source string.
    """
    try:
        # Compile will parse + compile all at once
        _ = compile(code, filename, "exec")
        return StateError(status=0, message="")

    except SyntaxError as e:
        # Capture the line of source and build a caret indicator
        src_line = e.text.rstrip("\n") if e.text else ""
        if e.offset and src_line:
            pointer = " " * (e.offset - 1) + "^"
            full_msg = f"{e.msg!r} at {filename}:{e.lineno}:{e.offset}\n    {src_line}\n    {pointer}"
        else:
            full_msg = f"{e.msg!r} at {filename}:{e.lineno}"
        return StateError(status=1, message=full_msg)

    except Exception as e:
        # Catch any other compile‑time error (though compile rarely raises non‑SyntaxError)
        return StateError(status=1, message=str(e))


def python_format(code: str) -> str:
    """Formats Python code using Black"""
    mode = black.FileMode(string_normalization=False)
    return black.format_str(code, mode=mode)


def sanitize_output(message: AIMessage) -> str:
    """
    Extracts executable code from an LLM response by:
     - Finding all ```…``` or ~~~…~~~ fenced blocks
     - Dedenting them
     - Removing any leading '>>>' or '...' prompts
     - Joining multiple blocks with a blank line
    If no fences are found, dedents and cleans the entire content.
    """
    content = message.content
    content = cast(str, content)  # to keep the type checker quiet

    def strip_prompts(code: str) -> str:
        lines = []
        for line in code.splitlines():
            if line.startswith(">>> "):
                lines.append(line[4:])
            elif line.startswith("... "):
                lines.append(line[4:])
            else:
                lines.append(line)
        return "\n".join(lines)

    # Regex to capture everything between ```…``` or ~~~…~~~ (non-greedy)
    fence_re = re.compile(r"(?:```|~~~)\s*\w*\n(.*?)(?:\n)?(?:```|~~~)", re.DOTALL)
    blocks = fence_re.findall(content)

    if blocks:
        cleaned = []
        for block in blocks:
            # remove common leading whitespace
            dedented = textwrap.dedent(block).strip()
            cleaned.append(strip_prompts(dedented))
        return "\n\n".join(cleaned)

    # No fences — assume the whole thing is code
    dedented_all = textwrap.dedent(content).strip()
    return strip_prompts(dedented_all)


def save_to_disk(code: str, path: str) -> None:
    """Saves code to specified path"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(code)
    logger.info(f"Saved code to {path}")
