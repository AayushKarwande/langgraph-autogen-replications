# LangGraph AutoGen Replications

Two small multi-agent systems built with [LangGraph](https://github.com/langchain-ai/langgraph), reproducing patterns from the AutoGen paper (dynamic group chat and human-in-the-loop escalation) without using the AutoGen library itself.

## Projects

- [`code-generator-agent/`](./code-generator-agent) — A group chat where a manager LLM routes between an Engineer, a Critic, and an Executor to write and run code that solves a task.
- [`math-agent/`](./math-agent) — A student assistant that escalates to a human expert (with an LLM go-between) when it's unsure or the student pushes back on its answer.

## Setup

Both projects share one environment.

```bash
python3 -m venv .venv
source .venv/bin/activate      # .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

You'll also need an OpenAI API key. Open either script and replace the placeholder in this line with your own key:

```python
llm = ChatOpenAI(model="gpt-4o-mini", api_key="your-key-here")
```

[LangSmith](https://smith.langchain.com) tracing is optional. To use it, replace the placeholder in `LANGSMITH_API_KEY` with your own key. To skip it, delete or comment out the three `LANGSMITH_*` lines near the top of each script.

## Running

```bash
python code-generator-agent/code_generator_agent.py
python math-agent/math_agent.py
```
