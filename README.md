# Decision Engine — Build vs Partner vs Acquire

An AI decision engine that takes a strategic goal like "We want to enter AI voice" and recommends whether your company should **Build**, **Partner**, or **Acquire** to gain that capability — backed by real **Crustdata** company, people, jobs, and funding data.

Scoring is deterministic and code-driven via `rubric.yaml`. The LLM is used only for translation and narrative, never for computing scores.

## How It Works

1. **Classify** — The LLM layer translates the free-text goal into a capability taxonomy (taxonomy tags, search keywords, signal descriptors). It does not score anything.
2. **Fetch** — The caching client retrieves Crustdata data for your company (enrichment, jobs, headcount) and searches for relevant candidates across all three paths. Every response is cached before touching scoring logic.
3. **Score** — The scoring engine evaluates each path (Build, Partner, Acquire) against criteria defined in `rubric.yaml`. Missing data for a criterion excludes it and renormalizes remaining weights — never defaulting to 0 or 5.
4. **Recommend** — The highest-scoring path wins. If the top two scores are within 1.0, it's flagged as a "close call" and both paths are presented with trade-offs.

Every score carries a provenance record: `{criterion_id, raw_value, source_field, api_call_id, timestamp}`.

## Architecture

```
/data      Crustdata client, response caching (SQLite), provenance wrapper
/scoring   Deterministic rubric engine — reads rubric.yaml, never calls the LLM
/llm       Prompt templates (versioned) + synthesis logic
/api       FastAPI routes
/cli       Entry point for demos
/tests     pytest with mocked Crustdata fixtures — no live API calls in CI
/docs      Architecture notes, rubric explanation, example run transcript
```

## Setup

### Prerequisites

- Python 3.11+
- A Crustdata API key
- A Groq API key (for LLM classification and narrative synthesis)

### Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Configuration

Copy the example env file and fill in your keys:

```bash
cp .env.example .env
# Edit .env with your API keys
```

| Variable | Description |
|---|---|
| `CRUSTDATA_API_KEY` | Crustdata Company API key |
| `GROQ_API_KEY` | Groq API key for LLM calls |

Never commit `.env`. The cache database is stored at `.cache/crustdata_cache.db` by default (gitignored).

## Usage

### CLI

```bash
python -m cli.main --my-company "Stripe" --capability "AI voice"
```

The CLI fetches your company's enrichment, jobs, and headcount, searches for candidates across all three paths, scores each path, and prints the recommendation with candidate lists and reasoning.

### API

Run the API server:

```bash
uvicorn api.main:app --reload
```

POST to `/analyze-strategy` with:

```json
{
  "my_company": "Stripe",
  "capability": "AI voice"
}
```

Returns per-path analysis with scores, reasoning, candidate lists, and estimated timeline/cost for building.

A `/health` endpoint is also available for uptime checks.

## Scoring Rubric

Weights and criteria are defined in [`rubric.yaml`](rubric.yaml). Each path has a `weight_in_final_decision` and a set of weighted criteria. The rubric is designed to be readable by reviewers without reading the Python code.

| Path | Weight | Key Criteria |
|---|---|---|
| **Build** | 0.34 | Internal hiring velocity, tech stack overlap, talent market availability, ecosystem maturity |
| **Partner** | 0.33 | Capability match, complementary customer base, decision-maker reachability, stability signal, integration friction |
| **Acquire** | 0.33 | Capability match, acquirable size, funding stage, team quality, decision-maker reachability |

See [`docs/rubric_explained.md`](docs/rubric_explained.md) for the full breakdown.

## Development

```bash
# Run tests (no network calls — all Crustdata data is mocked)
python -m pytest

# Lint
ruff check .

# Type check
mypy .
```

Test fixtures with mocked Crustdata responses live in [`tests/fixtures/`](tests/fixtures/).
