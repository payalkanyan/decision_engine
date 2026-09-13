# AGENTS.md — Build vs Partner vs Acquire Intelligence

This file is the shared context for any AI coding agent (Claude Code or
otherwise) working on this repository. Read this before making changes.
It is the source of truth for project intent, scope, and conventions —
if code and this file disagree, treat this file as correct and flag the
mismatch rather than silently resolving it.

## 1. What this project is

An AI decision engine that takes a goal like "We want to enter AI voice"
and recommends whether the requesting company should **Build**,
**Partner**, or **Acquire** to get that capability — backed by real
Crustdata company/people/jobs/funding/technographic data, not a single
LLM guess.

The core design principle: **scoring is deterministic and code-driven,
the LLM is used for translation and narrative, not for the numbers.**
The LLM turns the free-text goal into a capability taxonomy and turns
scored evidence into a written strategy. It never invents a score.

## 2. Non-goals for this version (explicitly out of scope)

Do not build these unless asked — they are documented "future work",
and scope creep here is the main risk to shipping this as a clean MVP:

- Full financial modeling of acquisition cost or valuation
- Legal/IP diligence
- Ongoing monitoring / alerting after a recommendation is made
- Coverage of every Crustdata endpoint — we use a deliberately narrow
  set of signals per path (see `rubric.yaml`)
- Multi-market / multi-goal batch comparison

## 3. Data sources (Crustdata)

Only use these endpoints unless a new one is explicitly approved and
added to `rubric.yaml`:

- Company Enrichment API — technographics, funding, headcount, web signals
- Company Search — filterable company graph
- Jobs API — real-time postings tied to company headcount/funding
- Headcount timeseries (by facet)
- Funding milestone timeseries
- Investor portfolio data
- Decision-makers filter / person screener
- LinkedIn posts (founder/team activity signal)
- Web traffic data

All Crustdata calls must go through the caching client in `/data` —
never call the API directly from scoring or LLM code. Credits are
metered; every uncached call should be intentional.

## 4. Architecture

```
/data      Crustdata client, response caching (SQLite/DuckDB), provenance wrapper
/scoring   Deterministic rubric engine, reads rubric.yaml, never calls the LLM
/llm       Prompt templates (versioned, not inline strings) + synthesis logic
/api       FastAPI routes, if/when exposed as a service or MCP tool
/cli       Entry point used for demos
/tests     pytest, with mocked Crustdata fixtures — no live API calls in CI
/docs      architecture diagram, rubric explanation, example run transcript
```

Every score produced by `/scoring` must carry a provenance record:
`{criterion_id, raw_value, source_field, api_call_id, timestamp}`.
If you write scoring logic that can't produce this, it's not done.

## 5. Coding conventions

- Type-safe schemas end to end (pydantic). No raw dicts crossing module
  boundaries.
- Every Crustdata response is cached before being touched by scoring logic.
- Missing data for a criterion → exclude and renormalize remaining
  weights (see `rubric.yaml` notes). Never silently default to 0 or 5.
- Prompts live in `/llm/prompts/` as versioned files (e.g.
  `synthesize_strategy_v1.md`), not as inline Python strings.
- No network calls inside test code — mock Crustdata responses in
  `/tests/fixtures`.
- Small, reviewable commits. One logical change per commit.
- Secrets only via `.env`, never committed. `.env.example` must stay
  in sync with any new required variable.

## 6. Definition of done for a feature

A feature is not done until:
1. It has a test with mocked data.
2. Its output includes provenance/evidence, not just a final number.
3. It's reflected in `rubric.yaml` if it changes scoring criteria.
4. README or `/docs` is updated if it changes the user-facing flow.

## 7. Reference documents in this repo

- `rubric.yaml` — the scoring rubric, source of truth for weights/criteria
- `CLAUDE.md` — Claude Code–specific session instructions (commands, workflow)
- `PROJECT_NOTES.md` — design rationale and the pre-launch checklist
