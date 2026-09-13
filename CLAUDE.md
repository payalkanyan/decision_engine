# CLAUDE.md

@AGENTS.md

This is the Claude Code entry point for this repo. The line above
imports AGENTS.md directly into context every session — Claude Code
does not read AGENTS.md on its own, so this import is what makes it
the real source of truth instead of a file that quietly goes stale.
Everything below is Claude Code–specific workflow that doesn't belong
in the shared, cross-tool agent spec.

## Session workflow

- Before writing code: state the plan in plain English (which files,
  which function, what test) and wait for confirmation on anything that
  touches `/scoring` or `rubric.yaml` — those define the actual
  decision logic and should not change silently.
- Work in small diffs. After each change: run the relevant tests, show
  the diff, then stop for review before moving to the next piece.
- Never call the live Crustdata API during development or in tests.
  Use/extend the fixtures in `/tests/fixtures`. Live calls are only for
  manual end-to-end demo runs, run explicitly by the human.
- If a task would require adding a new Crustdata endpoint not listed in
  AGENTS.md §3, stop and ask — don't silently expand data scope.

## Common commands

```bash
# install
pip install -r requirements.txt

# run tests (no live API calls)
pytest -q

# run the CLI against cached/mock data
python -m cli.main --goal "We want to enter AI voice" --dry-run

# run the CLI against the live Crustdata API (uses real credits)
python -m cli.main --goal "We want to enter AI voice"

# lint
ruff check .
```

## What "good" looks like in this repo

- A scoring change is accompanied by a `rubric.yaml` update explaining
  the new/changed criterion in plain English.
- A new prompt is added as a new versioned file in `/llm/prompts/`,
  not an edit that silently changes an existing version's behavior.
- Every PR-sized chunk of work includes at least one test.
- Output objects always carry an evidence trail — if you're tempted to
  return a bare score, add the provenance instead.

## Things to actively avoid

- Don't let the LLM compute or adjust a numeric score directly — it
  only interprets the goal and writes the narrative from scores that
  `/scoring` already produced.
- Don't fetch-and-score in the same function — keep data fetching,
  caching, scoring, and narrative generation in separate, testable
  layers per AGENTS.md's architecture.
- Don't expand scope beyond what's listed as in-scope in AGENTS.md §2
  without flagging it first.
