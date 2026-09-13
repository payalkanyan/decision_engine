# Taste Learnings

## Workflow

- Prefers a plan-first workflow: present a detailed plan for review, wait for approval, then implement in one pass. Do not start creating files until the plan is approved. Confidence: 0.9
- Wants explicit stop-and-wait gates between phases (e.g. scaffolding → stop → get approval → implement logic → stop → get approval). Do not proceed to the next phase without explicit go-ahead. Confidence: 0.9
- Insists that all reference/context files (e.g. AGENTS.md, CLAUDE.md, rubric specs) are read fully before doing any work. Confidence: 0.85
- Prefers scaffolding and architecture before business logic: folder structure, schemas, config files, and stubs first; scoring/fetching/LLM logic only after the scaffold is reviewed and approved. Confidence: 0.85
- When implementing a batch of work, prefers it done "in one pass" — all files created together rather than incrementally. Confidence: 0.75
