from types import CodeType
from typing import Any, Dict, Optional

from ..state import StateError


def python_compile(code: str, filename: str = "<string>") -> StateError:
    """
    Try to compile a Python source string.
    """
    try:
        # Compile will parse + compile all at once
        code_obj: CodeType = compile(code, filename, "exec")
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
