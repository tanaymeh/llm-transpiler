from pydantic import BaseModel, Field


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
