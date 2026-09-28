# Math Agent

A LangGraph system that solves a math question and knows when to ask for help. A **student assistant** LLM answers the question; if it's uncertain or the student isn't satisfied, it escalates to a human expert, who works with a second **expert assistant** LLM to turn their guidance into a clear response.

## How it works

1. The question is posted to the chat, and the student assistant attempts an answer.
2. You, playing the student, are prompted in the terminal to respond — confirm the answer, or push back if it's wrong.
3. If the assistant is unsure or you're not satisfied, it flags `NEED EXPERT`, and the chat hands off to the expert side.
4. You, now playing the expert, are prompted to give guidance. The expert assistant LLM turns that into a clear explanation and checks it with you before sending it back.
5. The student assistant folds the expert's guidance into an updated answer and asks you to confirm again.
6. Once you confirm, it responds with `FINAL ANSWER` and the run ends.

## Interactive by design

This script pauses and waits for terminal input (`Student:` and `Expert:` prompts) — that's expected, not a bug. It's meant to be run and answered live, not automated.

## Example question

The script ships with one example: a statics problem about a ladder leaning against a wall. Edit the `runner(...)` call at the bottom of `math_agent.py` to try a different question.

## Run it

```bash
python math_agent.py
```
