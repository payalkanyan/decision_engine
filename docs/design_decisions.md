# Design Decisions — Decision Engine

## What This Is

A data-driven engine that answers: **"Build versus Partner versus Acquire?"** when a company wants to enter a new capability like "AI voice."

CrustData doesn't just give data for talent acquisition teams — it can help companies decide whether to build a capability in-house, partner with a complementary company, or acquire a small specialized firm. So I built an engine that fetches real CrustData signals and scores each path deterministically.

## The Core Decision: Deterministic Scoring, LLM for Translation

Most AI projects let the LLM do the thinking and just say "I think you should partner." I separated the two:

| Layer | What it does | What it does NOT do |
|-------|-------------|---------------------|
| **LLM** (`groq/compound-mini`) | Translates free-text goals into structured taxonomies; writes narratives from already-computed scores | Never computes or adjusts numeric scores |
| **Scoring Engine** (Python + `rubric.yaml`) | Computes weighted scores from real CrustData data | Never calls the LLM |

**Why:** If the LLM scores things, output is non-reproducible and un-auditable. If the LLM only translates ("AI voice" → `[speech-to-text, voice-agents, real-time-audio]`) and synthesizes ("GCA scored 2.0/10 because..."), the numbers are deterministic and verifiable from raw data. This is the difference between "an AI said so" and "here's the evidence trail."

## Models Used

| Component | Model / Tech |
|-----------|-------------|
| Classification & Synthesis | `groq/compound-mini` (temp=0.3, JSON response format) |
| Cache | SQLite (SHA-256 keyed, per-endpoint TTLs) |
| API | FastAPI + Python 3.11+ |
| Frontend | Next.js 16 + React 19 + Tailwind CSS v4 |
| Schemas | Pydantic (strict type safety, end-to-end) |

## The Rubric (`rubric.yaml`)

Scoring logic lives in YAML, not hardcoded Python — so reviewers can read the decision logic without opening code.

**Three paths, 5 criteria each, 15 total:**

| Path | Weight | Criteria |
|------|--------|----------|
| **Build** | 0.34 | Hiring velocity, tech stack overlap, talent market availability, time-to-capability, ecosystem maturity penalty |
| **Partner** | 0.33 | Capability match, complementary customer base, decision-maker reachability, partnership stability, integration friction |
| **Acquire** | 0.33 | Capability match, acquirable size (5–50 employees ideal), funding stage, team quality, decision-maker reachability |

**Key rubric decisions:**

- **Weight renormalization** — if data is missing for a criterion (free tier returns 0/empty), that criterion is excluded and remaining weights redistributed proportionally. Never defaults to 0 or 5.
- **Close-call detection** — if top two path scores are within 1.0, both are presented with trade-offs instead of forcing a single answer.
- **0–10 scale per criterion** — raw CrustData values (employee count, funding) are mapped to a normalized scale via domain heuristics.

## Data Layer: Caching Is Cost Control

Every CrustData API call goes through `CachingClient`, which wraps a SQLite cache:

- SHA-256 deterministic keys (endpoint + params hash)
- Per-endpoint TTLs (company_enrichment = 24h, jobs = 1h, headcount = 7d)
- 5xx error caching with short TTL (5 min) — don't hammer a failing API
- Provenance records on every call: `{api_call_id, endpoint, params, timestamp}`

**Why this isn't trivial:** CrustData is a paid, credit-metered API. A single "analyze strategy" run makes 15+ API calls. Without caching, repeated runs burn through credits. Every cached response has a provenance record so you can trace any score back to the exact API call.

**People filtering** (`data/people_filters.py`) cleans noisy person data — keeps only senior titles (C-suite, VP, Head, Director, Founder), cross-checks founders against target company names, normalizes domain-to-company mappings. 40+ parametrized tests on real data.

## Why Should I Partner With Them?

This is the heart of the Partner path. When the engine recommends a partner, it shows the evidence, not just an opinion:

```
GCA Recruiting - Fit Score: 2.0/10
Reasoning: Score 2.0/10 based on size (0 employees) and funding ($0)

Key Signals:
  - Tech stack aligned with GCA
  - Funding stage: Series A+
  - Headcount: 20-200 range

Contact Info:
  - Partnerships team
  - Technical leadership
```

**The "why" is in the 5 weighted criteria:**

1. **Capability match** (30%) — does their tech/product match the target capability?
2. **Complementary customer base** (20%) — non-overlapping markets = co-selling; overlapping = direct competitor
3. **Decision-maker reachability** (25%) — named, reachable contacts at senior level
4. **Partnership stability** (15%) — stable entity, not distressed or about to be acquired
5. **Integration friction** (10%) — API-first vs closed platform, licensing model

Low scores like Partner at 1.7/10 are honest — most candidate recruiting companies have 0 employees or $0 funding under free-tier limits. The engine says "not able to access data, upgrade your plan" rather than making a recommendation on fabricated numbers.

## Differentiation From "Vibecoding"

| What a kid would build | What I built |
|----------------------|---------------|
| LLM chatbot giving opinions | Deterministic scoring engine with auditable evidence |
| Hardcoded path logic | Config-driven rubric — tunable without code changes |
| Fake or no data | Real CrustData API integration with caching + retries |
| No provenance | Every score carries `{criterion_id, raw_value, source_field, api_call_id, timestamp}` |
| LLM computes scores | LLM only translates and narrates; scores are code-computed |
| No error handling | Graceful degradation — missing data → exclude & renormalize |
| No tests | 89% test coverage, 12 test files, HTTP-transport mocking with `respx` |
| No type safety | Pydantic schemas end-to-end, mypy strict mode |
| Single output format | Structured `AnalysisOutput`: scores, candidates, provenance, assumptions/gaps |

**The real differentiator:** This engine produces **defensible recommendations**. A reviewer can ask "why Partner and not Build?" and point to the rubric, the raw CrustData data, and the provenance trail. You can't do that with an LLM opinion.

## Thinking Behind Key Decisions

**Why separate LLM from scoring?** Business strategy requires justifying recommendations to stakeholders. "The AI says partner" is not defensible. "Partner scored 1.7/10 because criterion X had value Y and weight Z, and here's the raw evidence" is defensible. The LLM is a translator and narrator, not a judge.

**Why YAML rubric?** The rubric *is* the product's strategic assumptions. If the GTM team wants to adjust how much weight "decision-maker reachability" gets, they should edit a YAML file — not open Python, find the right function, and risk regression. Same principle as config-driven feature flags.

**Why SQLite cache?** CrustData credits are metered. I can't lose cache state between deployments. SQLite is persistent, zero-config, and cache keys are deterministic hashes — same inputs always produce the same lookup. Redis would be faster but adds infrastructure complexity.

**Why not use LLM to find companies?** LLMs hallucinate company data — fake funding amounts, employee counts, contact names. By grounding every score in real CrustData API responses (cached and provenanced), I eliminate hallucination at the data layer. The LLM only writes the narrative summary of what the data shows.

**Why 0.34/0.33/0.33 weight split?** Intuitively near-equal so I don't bias toward any path — the data determines the recommendation. The slight Build preference (0.34) reflects that building is often the default assumption, and I want Partner/Acquire to have equal opportunity to win when the data supports them.

## Limitations & Future Work

- **Free tier data limitations** — CrustData's free API has limited coverage (company enrichment, headcount often return 0/empty). This is why scores are low. The engine is honest about missing data rather than making it up.
- **No financial modeling** — I score feasibility, not cost. Build cost analysis (salaries, infrastructure, time) is out of scope.
- **Single-market focus** — evaluates one goal at a time. Multi-goal batch comparison is future work.

---

