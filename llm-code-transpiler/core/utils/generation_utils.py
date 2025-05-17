import re
import textwrap
from typing import Any, cast

from langchain_core.messages import AIMessage


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
