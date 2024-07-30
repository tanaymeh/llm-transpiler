# LLM Transpiler
An attempt at building an LLM powered code-transpiler that follows a flow similar to [AlphaCodium](https://www.codium.ai/products/alpha-codium/) but using [Langgraph](https://langchain-ai.github.io/langgraph/) and commercial LLMs.

## Simple Transpile
![Simple Transpile](https://i.imgur.com/FEqC0Ha.png)

A basic version of transpiler can be found at [`src/simple_transpile.py`](https://github.com/tanaymeh/llm-code-transpiler/blob/main/src/simple_transpile.py). This version transpiles the code from Java to Python and then tries to parse the Python code using the AST module. If the code throws any compile-time errors, it captures the stack trace and sends it back to the "transpile" node along with the original code and a different prompt on how to deal with it.
