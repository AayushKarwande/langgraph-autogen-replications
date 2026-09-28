# Code Generator Agent

A LangGraph group chat that solves a coding task through three roles: an **Engineer** who writes the code, a **Critic** who reviews it, and an **Executor** who actually runs it. A **Manager** LLM reads the conversation after every turn and decides who speaks next, or ends the chat once the task is done.

## How it works

1. The task is posted to the chat.
2. The Manager picks the next speaker (Engineer, Critic, or Executor) or says `TERMINATE`.
3. The Engineer writes Python code in response to the task (or revises it based on feedback).
4. The Critic reviews the code without rewriting it.
5. The Executor finds the latest code block in the conversation and runs it with Python's `exec()`, capturing the output (or the error).
6. This loops, with the Manager deciding the next step each time, until the Manager terminates or `MAX_TURNS` (15) is hit.

## Note on `exec()`

The Executor runs whatever code the model writes, with no sandboxing. That's fine for this local demo, but don't point this at untrusted input or run it unmodified on a shared server.

## Example task

The script ships with one example: computing the mean, median, mode, and standard deviation of a list of numbers. Edit the `runner(...)` call at the bottom of `code_generator_agent.py` to try a different task.

## Run it

```bash
python code_generator_agent.py
```
