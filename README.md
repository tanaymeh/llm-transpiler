# LLM Transpiler
An attempt at building an LLM powered code-transpiler that follows a flow similar to [AlphaCodium](https://www.codium.ai/products/alpha-codium/) but using [Langgraph](https://langchain-ai.github.io/langgraph/) and commercial LLMs.

## Table of Contents
1. [Simple Transpile](#simple-transpile) - A minimal working version of transpiler that does transpiles the original code, tries compiling it and runs back-and-forth between the transpiler and compiler nodes until the code is error free.
2. [Complex Transpile](#complex-transpile) - A more advanced version that adds more nodes and more sophisticated logic to transpile code with higher precision.

## Simple Transpile
![Simple Transpile](https://i.imgur.com/FEqC0Ha.png)

A basic version of transpiler can be found at [`src/simple_transpile.py`](https://github.com/tanaymeh/llm-code-transpiler/blob/main/src/simple_transpile.py). This version transpiles the code from Java to Python and then tries to parse the Python code using the AST module. If the code throws any compile-time errors, it captures the stack trace and sends it back to the "transpile" node along with the original code and a different prompt on how to deal with it.


## Complex Transpile
![Complex Transpile](https://i.imgur.com/sWrfeMM.png)

A more complex version of transpiler can be found at [`src/complex_transpile.py`](https://github.com/tanaymeh/llm-code-transpiler/blob/main/src/complex_transpile.py). This version, builts on top of small transpiler by adding a summary node as the entry point of the graph and a formatter at the end of the graph.

The original code first flows into the summary node which uses an LLM to generate a concise, technical summary of the original code file including details about what each class and function does. This summary then, along with the original code is sent to the transpile node and then process continues as normal.

The final node is a format node which uses Black formatter in Python to format the code at the end of successful compilation to meet the PEP8 standards.
 
This version is currently under work.