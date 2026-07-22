# Self-Healing Codebase Agent

An AI agent that fixes broken code by actually verifying its own work — not just guessing once and stopping. It runs the test suite, reads the real failure, proposes a fix, reapplies, and reruns — looping until the tests genuinely pass (or it hits a limit and gives up gracefully).

Built for OpenAI Build Week 2026.

## Why this is different from typical "AI code fix" tools

Most AI coding tools work in a single shot: you ask for a fix, you get one, and there's no verification it's actually correct. This agent instead follows a **verify-before-trust loop** — the same core principle behind real autonomous coding agents, not just chat-style tools:

1. Run the existing tests
2. If they fail, capture the *exact* error
3. Send the code + error to a local AI model, ask for a fix
4. Apply the fix, rerun the tests
5. If still failing, repeat with the new error (up to 5 attempts)
6. Log every attempt — code before, error, proposed fix — to a JSON file for a full reasoning trail

## Tech stack

- Python
- `pytest` for verification (the ground truth the agent checks itself against)
- [Ollama](https://ollama.com) running Llama 3.2 (3B) locally — no paid API, runs fully offline

## Example: watch it work

Given this buggy function:

\```python
def calculate_average(numbers):
    total = sum(numbers)
    return total / len(numbers) + 1  # bug
\```

Running the agent:

\```
python agent.py calculator.py test_calculator.py
\```

Produces this trail:

- **Attempt 1:** Tests fail (`assert 3.0 == 2`) → agent reads the error → proposes removing the extra `+ 1`
- **Attempt 2:** Tests pass ✅

Full reasoning trail (including the exact prompt context and fix) is saved to `logs/`.

## Bugs tested

| File | Bug | Difficulty |
|---|---|---|
| `calculator.py` | Simple arithmetic bug (extra `+1`) | Easy |
| `string_utils.py` | Palindrome check ignoring docstring intent (case/spaces) | Medium — requires inferring intent, not just syntax |
| `inventory.py` | Two separate bugs across two functions (wrong discount formula + ignored quantity) | Harder — multiple distinct fixes in one file |

All three were resolved automatically, with full logs in `logs/`.

## Running it yourself

1. Install [Ollama](https://ollama.com/download) and pull the model:
   \```
   ollama pull llama3.2:3b
   \```
2. Set up the Python environment:
   \```
   python -m venv venv
   venv\Scripts\activate   # Windows
   pip install -r requirements.txt
   \```
3. Run the agent on all known bugs:
   \```
   python agent.py
   \```
   Or on a specific file:
   \```
   python agent.py calculator.py test_calculator.py
   \```

## What's next

- Extend beyond single-file bugs to multi-file codebases
- Add a categorization layer (what *type* of bug was it — logic, off-by-one, wrong formula, etc.) to build a pattern-recognition memory over time
- Swap in different local models to compare fix quality vs. speed